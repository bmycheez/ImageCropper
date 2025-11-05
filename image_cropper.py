import numpy as np
import os
from tkinter import Tk, filedialog, simpledialog, messagebox
from PIL import Image
import matplotlib
matplotlib.use('QtAgg') 
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
import matplotlib.font_manager as fm 

# --- Matplotlib 한글 폰트 설정 ---
FONT_NAME = 'Malgun Gothic' 
plt.rcParams['font.family'] = FONT_NAME
plt.rcParams['axes.unicode_minus'] = False 

# --- 설정 변수 ---
CROP_WIDTH = 1024
CROP_HEIGHT = 1024
FOLDER_PATH = None
OUTPUT_FOLDER = None
IMAGE_FILES = []
CURRENT_INDEX = -1
ORIGINAL_IMAGE_PIL = None     
DISPLAY_IMAGE_PIL = None      
MAX_DISPLAY_PIXELS = 2048     

FIG, AX = None, None 
pan_start_x, pan_start_y = None, None 
# ⭐ 추가: 현재 크롭 영역을 추적하는 변수
current_crop_rect = None
is_transitioning = False  # ⭐ 새로운 전역 플래그

root = Tk()
root.withdraw()

# --- Matplotlib 이벤트 콜백 함수 ---

def execute_crop(start_x, start_y):
    """크롭 로직을 실행하고 저장합니다."""
    
    if ORIGINAL_IMAGE_PIL is None or OUTPUT_FOLDER is None:
        messagebox.showerror("오류", "폴더 선택 또는 이미지 로드 상태를 확인하세요.")
        return

    left = start_x
    upper = start_y
    right = left + CROP_WIDTH
    lower = upper + CROP_HEIGHT

    original_w, original_h = ORIGINAL_IMAGE_PIL.size
    if right > original_w or lower > original_h or left < 0 or upper < 0:
        messagebox.showerror("오류", "크롭 영역이 이미지 경계를 벗어납니다.")
        return
        
    cropped_img_pil = ORIGINAL_IMAGE_PIL.crop((left, upper, right, lower))
    
    file_name = IMAGE_FILES[CURRENT_INDEX]
    base_name, ext = os.path.splitext(file_name)
    # 크롭 시작 좌표를 파일명에 추가
    save_file_name = f"{base_name}_x-{left}_y-{upper}{ext}" 
    save_path = os.path.join(OUTPUT_FOLDER, save_file_name)
    
    try:
        cropped_img_pil.save(save_path)
        print(f"✅ 저장 완료: {save_file_name}")
        highlight_crop_area(left, upper)
        
    except Exception as e:
        # ⭐ 저장 오류 메시지 처리
        print(f"❌ 저장 오류: {e}")
        messagebox.showerror("저장 오류", f"이미지 저장 실패: {e}")
    
    # 크롭 후 시각화 업데이트
    highlight_crop_area(left, upper)

# --- highlight_crop_area 함수 (수정) ---
def highlight_crop_area(start_x, start_y):
    """크롭이 완료된 후 청록색 틀을 크롭된 위치에 맞춰 이동시킵니다."""
    global AX, current_crop_frame
    
    # 뷰포트의 중앙으로 이동하지 않고, 틀만 크롭된 위치로 이동시킵니다.
    
    # 현재 뷰포트를 크롭된 영역으로 이동 (시각적 피드백)
    original_w, original_h = ORIGINAL_IMAGE_PIL.size
    display_w, display_h = DISPLAY_IMAGE_PIL.size
    
    # 크롭된 영역을 Display 이미지 좌표로 변환
    rect_x = (start_x / original_w) * display_w
    rect_y = (start_y / original_h) * display_h
    rect_w = (CROP_WIDTH / original_w) * display_w
    rect_h = (CROP_HEIGHT / original_h) * display_h
    
    # ⭐ 청록색 틀을 크롭된 위치에 맞춰 업데이트
    if current_crop_frame:
        current_crop_frame.set_xy((rect_x, rect_y))
        current_crop_frame.set_width(rect_w)
        current_crop_frame.set_height(rect_h)

    # 뷰포트를 크롭된 영역 주변으로 이동
    AX.set_xlim(rect_x - rect_w * 0.5, rect_x + rect_w * 1.5)
    AX.set_ylim(rect_y + rect_h * 1.5, rect_y - rect_h * 0.5)

    plt.title(f"크롭 완료. 시작점: ({start_x}, {start_y}). 'N' 키로 다음 이미지.", fontsize=10)
    FIG.canvas.draw_idle()


def pan_handler(event):
    """마우스 드래그를 사용하여 뷰포트 이동 (릴리즈 시점 업데이트)."""
    global pan_start_x, pan_start_y, AX
    
    if event.xdata is None or event.ydata is None:
        return
    
    if event.button is MouseButton.LEFT:
        if event.name == 'button_press_event':
            pan_start_x = event.xdata
            pan_start_y = event.ydata

        elif event.name == 'button_release_event' and pan_start_x is not None:
            dx = event.xdata - pan_start_x
            dy = event.ydata - pan_start_y
            
            x_min, x_max = AX.get_xlim()
            y_max, y_min = AX.get_ylim() # y_min < y_max
            
            new_x_min = x_min - dx
            new_x_max = x_max - dx
            new_y_min = y_min - dy
            new_y_max = y_max - dy

            display_w, display_h = DISPLAY_IMAGE_PIL.size
            
            # 뷰포트 경계 조정 (Display 이미지 경계를 벗어나지 않도록)
            if new_x_min < 0:
                dx_adj = 0 - new_x_min
                new_x_min, new_x_max = new_x_min + dx_adj, new_x_max + dx_adj
            elif new_x_max > display_w:
                dx_adj = display_w - new_x_max
                new_x_min, new_x_max = new_x_min + dx_adj, new_x_max + dx_adj
            
            if new_y_min < 0:
                dy_adj = 0 - new_y_min
                new_y_min, new_y_max = new_y_min + dy_adj, new_y_max + dy_adj
            elif new_y_max > display_h:
                dy_adj = display_h - new_y_max
                new_y_min, new_y_max = new_y_min + dy_adj, new_y_max + dy_adj
            
            # --- 뷰포트 업데이트 ---
            AX.set_xlim(new_x_min, new_x_max)
            AX.set_ylim(new_y_max, new_y_min)
            
            # ⭐⭐ 크롭 틀을 현재 뷰포트 중앙에 재배치하는 로직 추가 ⭐⭐
            update_crop_frame()
            
            FIG.canvas.draw_idle() 
            pan_start_x, pan_start_y = None, None

def crop_and_zoom_handler(event):
    """스크롤 줌 기능과 오른쪽 클릭 크롭을 처리합니다."""
    
    # 1. 스크롤 줌 처리
    if event.name == 'scroll_event':
        x_data, y_data = event.xdata, event.ydata
        if x_data is None or y_data is None: return
        
        scale_factor = 1.2 
        
        x_min, x_max = AX.get_xlim()
        y_max, y_min = AX.get_ylim()

        if event.button == 'up': # 확대 (Zoom In)
            new_x_min = x_data - (x_data - x_min) / scale_factor
            new_x_max = x_data + (x_max - x_data) / scale_factor
            new_y_min = y_data - (y_data - y_min) / scale_factor
            new_y_max = y_data + (y_max - y_data) / scale_factor
        elif event.button == 'down': # 축소 (Zoom Out)
            new_x_min = x_data - (x_data - x_min) * scale_factor
            new_x_max = x_data + (x_max - x_data) * scale_factor
            new_y_min = y_data - (y_data - y_min) * scale_factor
            new_y_max = y_data + (y_max - y_data) * scale_factor

        # 뷰포트 업데이트
        AX.set_xlim(new_x_min, new_x_max)
        AX.set_ylim(new_y_max, new_y_min) 
        
        # ⭐⭐ 크롭 틀을 현재 뷰포트 중앙에 재배치하는 로직 추가 ⭐⭐
        update_crop_frame()

        FIG.canvas.draw_idle()


    # 2. 오른쪽 클릭 = 크롭 실행
    if event.name == 'button_press_event' and event.button is MouseButton.RIGHT:
        if event.xdata is None or event.ydata is None: return
        
        # ⭐⭐⭐ 핵심 수정: 크롭 시작 좌표를 청록색 점선 틀의 위치로 설정 ⭐⭐⭐
        if current_crop_frame is None:
             messagebox.showerror("오류", "크롭 틀이 초기화되지 않았습니다.")
             return

        # 청록색 틀의 왼쪽 상단 좌표 (Display 이미지 기준)
        frame_x_start, frame_y_start = current_crop_frame.get_xy()
        
        original_w, original_h = ORIGINAL_IMAGE_PIL.size
        display_w, display_h = DISPLAY_IMAGE_PIL.size

        # 좌표 변환 비율
        scale_x = original_w / display_w
        scale_y = original_h / display_h

        # 변환된 크롭 시작 좌표 (원본 이미지 기준)
        left = int(frame_x_start * scale_x)
        upper = int(frame_y_start * scale_y)
        
        # 크롭 실행
        execute_crop(left, upper)

# --- ⭐⭐ 새로운 보조 함수 추가 (크롭 틀 위치 계산) ⭐⭐ ---
def update_crop_frame():
    """크롭 틀을 현재 뷰포트의 중앙에 위치시키고 크기를 조정합니다."""
    global AX, current_crop_frame
    
    if not current_crop_frame:
        return
        
    # 현재 뷰포트의 중앙점 (Display 이미지 좌표계)
    x_min, x_max = AX.get_xlim()
    y_max, y_min = AX.get_ylim()
    
    view_center_x = (x_min + x_max) / 2
    view_center_y = (y_min + y_max) / 2

    # 뷰포트의 실제 폭과 높이
    view_width = x_max - x_min
    view_height = y_max - y_min
    
    # 크롭 틀의 크기를 현재 뷰포트 비율에 맞게 조정
    display_w, display_h = DISPLAY_IMAGE_PIL.size
    original_w, original_h = ORIGINAL_IMAGE_PIL.size

    # 크롭 틀의 크기 (Display 이미지 기준으로 계산)
    scale_x = display_w / original_w
    scale_y = display_h / original_h

    rect_w = CROP_WIDTH * scale_x
    rect_h = CROP_HEIGHT * scale_y
    
    # 크롭 틀의 새로운 왼쪽 상단 좌표 (뷰포트 중앙 기준)
    new_x = view_center_x - rect_w / 2
    new_y = view_center_y - rect_h / 2
    
    # 크롭 틀 위치와 크기를 업데이트
    current_crop_frame.set_xy((new_x, new_y))
    current_crop_frame.set_width(rect_w)
    current_crop_frame.set_height(rect_h)

# --- key_handler 함수 수정 ---
def key_handler(event):
    """키보드 'N'을 눌러 다음 이미지로 이동합니다."""
    global FIG, is_transitioning
    
    if event.key.upper() == 'N':
        # ⭐ N 키를 누르면 전환 중 플래그를 True로 설정
        is_transitioning = True
        
        # plt.close(FIG)를 호출하면 close_event가 발생하지만,
        # is_transitioning 플래그 때문에 close_handler에서 sys.exit()이 무시됩니다.
        plt.close(FIG)
        
        # 다음 이미지 로드 (이 함수 내에서 is_transitioning은 load_next_image가 호출되기 전까지 True를 유지)
        load_next_image()
        
        # load_next_image가 성공적으로 새 창을 띄우고 나면,
        # is_transitioning을 False로 설정할 수도 있지만,
        # close_handler에서 reset하는 것이 더 안전합니다.

# --- 기타 로직 함수 (생략) ---

def select_folder(is_output=False):
    """원본 또는 저장 폴더를 선택하고 이미지 목록을 로드합니다."""
    global FOLDER_PATH, OUTPUT_FOLDER, IMAGE_FILES, CURRENT_INDEX
    
    # ... (기존 폴더 선택 로직 유지) ...
    title = "크롭 이미지 저장 폴더 선택" if is_output else "원본 이미지 폴더 선택"
    folder_path = filedialog.askdirectory(title=title, parent=root)
    
    if folder_path:
        if is_output:
            OUTPUT_FOLDER = folder_path
            print(f"저장 폴더: {folder_path}")
            messagebox.showinfo("저장 폴더", f"크롭 이미지는 '{os.path.basename(folder_path)}'에 저장됩니다.")
        else:
            FOLDER_PATH = folder_path
            print(f"원본 폴더: {folder_path}")
            
            if OUTPUT_FOLDER is None:
                OUTPUT_FOLDER = FOLDER_PATH
                print(f"저장 폴더가 지정되지 않아 원본 폴더로 설정됨.")

            image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
            IMAGE_FILES.clear()
            for f in sorted(os.listdir(FOLDER_PATH)):
                if os.path.splitext(f)[1].lower() in image_extensions:
                    IMAGE_FILES.append(f)
            
            if not IMAGE_FILES:
                messagebox.showinfo("정보", "선택한 폴더에 이미지가 없습니다.")
                CURRENT_INDEX = -1
                return

            load_next_image(start_index=-1)

def set_crop_size():
    """크롭할 크기를 설정합니다."""
    global CROP_WIDTH, CROP_HEIGHT
    try:
        new_size = simpledialog.askstring("크기 설정", "새로운 크기를 입력하세요 (예: 1024x1024):", parent=root)
        if new_size:
            w, h = map(int, new_size.lower().split('x'))
            CROP_WIDTH = w
            CROP_HEIGHT = h
            print(f"설정된 크롭 크기: {CROP_WIDTH}x{CROP_HEIGHT}")
            
            # 크롭 크기 변경 후 현재 뷰포트를 새로운 크기에 맞게 재설정 시도
            if AX:
                x_center = int(np.mean(AX.get_xlim()))
                y_center = int(np.mean(AX.get_ylim()))
                AX.set_xlim(x_center - CROP_WIDTH/2, x_center + CROP_WIDTH/2)
                AX.set_ylim(y_center + CROP_HEIGHT/2, y_center - CROP_HEIGHT/2)
                FIG.canvas.draw_idle()

    except Exception:
        messagebox.showerror("오류", "잘못된 형식입니다. '가로x세로' 형식으로 입력하세요.")


# --- 로드 및 디스플레이 ---

def load_next_image(start_index=None):
    """다음 이미지 로드 및 표시."""
    global CURRENT_INDEX, ORIGINAL_IMAGE_PIL, DISPLAY_IMAGE_PIL, FIG, AX

    if start_index is not None:
        CURRENT_INDEX = start_index
    else:
        CURRENT_INDEX += 1
    
    if CURRENT_INDEX >= len(IMAGE_FILES):
        plt.close('all')
        messagebox.showinfo("완료", "모든 이미지 처리를 완료했습니다.")
        return
        
    file_name = IMAGE_FILES[CURRENT_INDEX]
    file_path = os.path.join(FOLDER_PATH, file_name)
    
    print(f"\n--- 로드 중: {CURRENT_INDEX + 1}/{len(IMAGE_FILES)} - {file_name} ---")

    try:
        # ⭐⭐ 이미지 로드 수정: load() 명시적 호출 추가 (BMP 오류 방지) ⭐⭐
        img = Image.open(file_path)
        img.load() 
        ORIGINAL_IMAGE_PIL = img.convert("RGB") 
        
        original_w, original_h = ORIGINAL_IMAGE_PIL.size

        if original_w > MAX_DISPLAY_PIXELS or original_h > MAX_DISPLAY_PIXELS:
            ratio = MAX_DISPLAY_PIXELS / max(original_w, original_h)
            temp_w = int(original_w * ratio)
            temp_h = int(original_h * ratio)
            
            DISPLAY_IMAGE_PIL = ORIGINAL_IMAGE_PIL.resize((temp_w, temp_h), Image.Resampling.LANCZOS)
        else:
            DISPLAY_IMAGE_PIL = ORIGINAL_IMAGE_PIL.copy()

        display_image()

    except Exception as e:
        print(f"❌ 이미지 로드 실패: {file_name}\n오류: {e}")
        # ⭐ 로드 오류 메시지 처리
        messagebox.showerror("오류", f"이미지 로드 실패: {file_name}\n오류: {e}")
        load_next_image()

# --- close_handler 함수 수정 ---
def close_handler(event):
    """Matplotlib 창이 닫힐 때 프로그램을 종료합니다. N 키 전환 중에는 종료하지 않습니다."""
    global root, is_transitioning
    
    if is_transitioning:
        # N 키를 눌러 다음 이미지로 넘어가는 중이라면, 종료하지 않고 return합니다.
        is_transitioning = False # 플래그 초기화
        return

    print("Matplotlib 창 닫힘 감지. 프로그램을 종료합니다.")
    try:
        root.quit() 
    except Exception:
        pass
    
    import sys
    sys.exit()

# --- 전역 변수 초기화에 추가 ---
current_crop_frame = None # 크롭 영역 테두리 객체

# --- display_image 함수 수정 (크롭 틀 초기 표시) ---
def display_image():
    global FIG, AX, current_crop_frame
    
    if FIG:
        plt.close(FIG) 
    
    # 캔버스 크기 (기존 로직 유지)
    plt.rcParams["figure.figsize"] = (CROP_WIDTH / 100, CROP_HEIGHT / 100) 
    plt.rcParams["figure.dpi"] = 100 
    
    FIG, AX = plt.subplots()
    
    AX.imshow(DISPLAY_IMAGE_PIL) 
    AX.axis('off') 
    
    display_w, display_h = DISPLAY_IMAGE_PIL.size
    
    # 뷰 포트를 Display 이미지의 전체 크기로 초기화 (스크롤 줌 위해)
    AX.set_xlim(0, display_w)
    AX.set_ylim(display_h, 0)
    AX.set_aspect('equal', adjustable='box') 

    # ⭐⭐ 1. 크롭 틀 초기 위치 계산 (Display 이미지 중앙) ⭐⭐
    center_x = display_w / 2
    center_y = display_h / 2
    
    # 크롭 틀 크기 (Display 이미지 기준으로 계산)
    original_w, original_h = ORIGINAL_IMAGE_PIL.size
    scale_x = display_w / original_w
    scale_y = display_h / original_h

    rect_w = CROP_WIDTH * scale_x
    rect_h = CROP_HEIGHT * scale_y
    
    # 크롭 틀의 왼쪽 상단 좌표
    rect_x_start = center_x - rect_w / 2
    rect_y_start = center_y - rect_h / 2
    
    # 크롭 틀을 뷰포트 중앙에 그립니다.
    current_crop_frame = plt.Rectangle((rect_x_start, rect_y_start), rect_w, rect_h,
                                        edgecolor='cyan', facecolor='none', linewidth=3, linestyle='--')
    AX.add_patch(current_crop_frame)

    plt.title(f"파일: {IMAGE_FILES[CURRENT_INDEX]} | 크롭 크기: {CROP_WIDTH}x{CROP_HEIGHT}\n(왼쪽 드래그=이동, 스크롤=확대/축소, 오른쪽 클릭=크롭)", fontsize=10)
    
    # 이벤트 핸들러 연결은 유지
    FIG.canvas.mpl_connect('button_press_event', pan_handler)
    FIG.canvas.mpl_connect('button_release_event', pan_handler)
    FIG.canvas.mpl_connect('button_press_event', crop_and_zoom_handler) 
    FIG.canvas.mpl_connect('scroll_event', crop_and_zoom_handler)
    FIG.canvas.mpl_connect('key_press_event', key_handler)

    # ⭐⭐ Matplotlib 창 닫힘 이벤트를 close_handler에 연결 ⭐⭐
    FIG.canvas.mpl_connect('close_event', close_handler)

    plt.show(block=False) 
    FIG.canvas.draw_idle()

def setup_menu():
    """사용자에게 옵션을 제공하는 간단한 콘솔 메뉴입니다."""
    print("\n" + "="*50)
    print("      Matplotlib 기반 이미지 크롭 도구 (고속 뷰포트)")
    print("="*50)
    print("1. 원본 폴더 선택 (필수)")
    print("2. 저장 폴더 선택 (선택, 미선택 시 원본 폴더)")
    print("3. 크롭 크기 설정 (현재: {}x{})".format(CROP_WIDTH, CROP_HEIGHT))
    print("N. 다음 이미지 로드 (콘솔 입력 또는 이미지 창에서 N 키)")
    print("Q. 종료 (Q 또는 q)")
    print("-" * 50)
    print("이미지 윈도우 조작: 왼쪽 드래그=이동, 스크롤=확대/축소, 오른쪽 클릭=크롭")
    print("="*50)

# --- 메인 실행 루프 (생략) ---
def main_loop():
    setup_menu()
    
    select_folder(is_output=False)
    
    if not FOLDER_PATH:
        print("원본 폴더 선택이 취소되어 프로그램을 종료합니다.")
        return

    while True:
        try:
            user_input = input("옵션을 입력하세요 (N/Q/1/2/3): ").strip().upper()
        except EOFError:
            break
        
        if user_input == 'Q':
            break
        elif user_input == 'N':
            if FIG:
                 plt.close(FIG)
            load_next_image()
        elif user_input == '1':
            select_folder(is_output=False)
        elif user_input == '2':
            select_folder(is_output=True)
        elif user_input == '3':
            set_crop_size()
        else:
            print("잘못된 입력입니다.")
        
    # ⭐⭐ 기존 종료 로직 제거 또는 수정 ⭐⭐
    # 만약 main_loop가 종료되면 sys.exit()을 호출하여 확실하게 종료합니다.
    # ⭐ Q 또는 EOF로 루프가 끝났을 때만 종료
    plt.close('all')
    root.destroy()
    print("프로그램이 종료되었습니다.")
    import sys
    sys.exit()


if __name__ == "__main__":
    main_loop()
