import adsk.core, adsk.fusion, traceback
import time
import math
import os

# --- 核心函数1：根据当前视图动态计算坐标轴和距离 ---
def get_dynamic_axes(app):
    """
    捕获当前相机视角，计算并返回动态坐标轴（方向向量）、目标点和合适的相机距离。
    """
    viewport = app.activeViewport
    camera = viewport.camera
    
    initial_camera_state = {
        'eye': camera.eye.copy(),
        'target': camera.target.copy(),
        'up': camera.upVector.copy()
    }
    
    viewport.fit()
    adsk.doEvents()
    time.sleep(0.1)
    
    scale_factor = 0.9
    camera.viewExtents = camera.viewExtents / scale_factor
    viewport.camera = camera
    adsk.doEvents()
    distance = viewport.camera.viewExtents * 3 
    if distance < 1: distance = 10

    eye = initial_camera_state['eye']
    target = initial_camera_state['target']
    up_vector = initial_camera_state['up']
    
    view_dir = target.vectorTo(eye)
    view_dir.normalize()

    right_dir = up_vector.crossProduct(view_dir)
    right_dir.normalize()

    final_up_dir = view_dir.crossProduct(right_dir)
    final_up_dir.normalize()
    
    return {
        'front': view_dir,
        'right': right_dir,
        'up': final_up_dir,
        'target': target,
        'distance': distance
    }

# --- 核心函数2：瞬时切换并保存六视图 ---
def show_and_save_standard_views(app, axes, save_directory, width, height):
    ui = app.userInterface
    try:
        viewport = app.activeViewport
        camera = viewport.camera
        
        distance = axes['distance']
        target_point = axes['target']
        front_vec = axes['front']
        right_vec = axes['right']
        up_vec = axes['up']

        top_view_up_vector = front_vec.copy()
        top_view_up_vector.scaleBy(-1)

        view_definitions = [
            {"name": "Front",  "eye": target_point.copy(), "up": up_vec, "dir": front_vec},
            {"name": "Back",   "eye": target_point.copy(), "up": up_vec, "dir": front_vec.copy()},
            {"name": "Right",  "eye": target_point.copy(), "up": up_vec, "dir": right_vec.copy()},
            {"name": "Left",   "eye": target_point.copy(), "up": up_vec, "dir": right_vec.copy()},
            {"name": "Top",    "eye": target_point.copy(), "up": top_view_up_vector, "dir": up_vec.copy()},
            {"name": "Bottom", "eye": target_point.copy(), "up": front_vec.copy(), "dir": up_vec.copy()}
        ]
        
        directions = [(1), (-1), (1), (-1), (1), (-1)]
        for i, view in enumerate(view_definitions):
            vec = view['dir'].copy()
            vec.scaleBy(distance * directions[i])
            view['eye'].translateBy(vec)

        for view in view_definitions:
            view_name = view['name']
            print(f"正在处理视图: {view_name}")
            
            camera.eye = view["eye"]
            camera.target = target_point
            camera.upVector = view["up"]
            camera.isOrthographic = True
            viewport.camera = camera
            adsk.doEvents()
            time.sleep(0.1)

            # 修改为 .jpg 格式
            screenshot_path = os.path.join(save_directory, f"{view_name}.jpg")
            viewport.saveAsImageFile(screenshot_path, width, height)
        
        print("六视图已全部导出。")

    except Exception as e:
        if ui:
            ui.messageBox(f"show_and_save_standard_views 失败:\n{traceback.format_exc()}")

# --- 核心函数3：切换并保存多个透视图 (可缩放) ---
def show_and_save_perspective_views(app, axes, zoom_factor, save_directory, width, height):
    ui = app.userInterface
    try:
        viewport = app.activeViewport
        camera = viewport.camera
        delay_time = 0.2

        target_point = axes['target']
        front_vec = axes['front']
        right_vec = axes['right']
        up_vec = axes['up']

        # === 透视图1：动态 Front-Top-Right 角度 ===
        print("正在处理动态透视图1...")
        
        v1 = right_vec.copy(); v1.scaleBy(8)
        v2 = front_vec.copy(); v2.scaleBy(8)
        v3 = up_vec.copy(); v3.scaleBy(6)
        
        total_vec = v1; total_vec.add(v2); total_vec.add(v3)
        
        persp_eye_1 = target_point.copy()
        persp_eye_1.translateBy(total_vec)

        camera.eye = persp_eye_1
        camera.target = target_point
        camera.upVector = up_vec
        camera.isOrthographic = False
        viewport.camera = camera
        viewport.refresh()
        time.sleep(delay_time)

        viewport.fit()
        adsk.doEvents()
        
        if zoom_factor != 1.0:
            camera.viewExtents *= zoom_factor
            viewport.camera = camera
            adsk.doEvents()
            time.sleep(0.1)

        # 修改为 .jpg 格式
        screenshot_path = os.path.join(save_directory, "Perspective_01_Dynamic.jpg")
        viewport.saveAsImageFile(screenshot_path, width, height)

        # === 透视图2：动态 Back-Left-Bottom 角度 ===
        print("正在处理动态透视图2...")
        v1 = right_vec.copy(); v1.scaleBy(-8)
        v2 = front_vec.copy(); v2.scaleBy(-8)
        v3 = up_vec.copy(); v3.scaleBy(-6)

        total_vec = v1; total_vec.add(v2); total_vec.add(v3)

        persp_eye_2 = target_point.copy()
        persp_eye_2.translateBy(total_vec)
        
        camera.eye = persp_eye_2
        camera.target = target_point
        camera.upVector = up_vec
        viewport.camera = camera
        viewport.refresh()
        time.sleep(delay_time)

        viewport.fit()
        adsk.doEvents()
        
        if zoom_factor != 1.0:
            camera.viewExtents *= zoom_factor
            viewport.camera = camera
            adsk.doEvents()
            viewport.refresh()    # 强制要求视口重绘光影
            time.sleep(0.5)
        
        # 修改为 .jpg 格式
        screenshot_path = os.path.join(save_directory, "Perspective_02_Dynamic.jpg")
        viewport.saveAsImageFile(screenshot_path, width, height)

    except Exception as e:
        if ui:
            ui.messageBox(f"show_and_save_perspective_views 失败:\n{traceback.format_exc()}")


# --- 主运行函数 ---
def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        product = app.activeProduct
        if not product or product.productType != 'DesignProductType':
            if ui: ui.messageBox("请先打开一个设计文件！")
            return

        # --- 用户可配置参数 ---
        save_directory = r"C:\Users\Windows10\Desktop\A"
        
        # ========== 🎯 在这里修改图片的分辨率 (宽度和高度) ==========
        image_width = 2480
        image_height = 3508
        
        # ========== 🎯 在这里修改透视图的缩放比例 ==========
        #  < 1.0 : 模型更大 (放大)
        #  > 1.0 : 模型更小 (缩小)
        #  = 1.0 : 默认大小
        PERSPECTIVE_ZOOM_FACTOR = 1.001
        
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        # --- 核心流程 ---
        print("捕获当前视图作为基准...")
        dynamic_axes = get_dynamic_axes(app)

        print("第一步：开始生成并导出六视图...")
        show_and_save_standard_views(app, dynamic_axes, save_directory, image_width, image_height)
        
        print("第二步：开始生成并导出动态透视图...")
        show_and_save_perspective_views(app, dynamic_axes, PERSPECTIVE_ZOOM_FACTOR, save_directory, image_width, image_height)

        print(f"任务完成！\n所有图片已保存至: {save_directory}")

    except Exception as e:
        if ui:
            ui.messageBox('脚本运行失败:\n{}'.format(traceback.format_exc()))
