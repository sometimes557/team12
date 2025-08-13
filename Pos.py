import os
import importlib.util

# 手动指定模块执行顺序
files = ['ymx_get_id.py', 'ymx_pac.py','analysis.py']
folder_path = "E:\Pycharm\team12"  # 需替换为实际路径

for file in files:
    file_path = os.path.join(folder_path, file)

    # 1️⃣ 创建模块规范（Spec）
    spec = importlib.util.spec_from_file_location(
        name=file[:-3],  # 模块名（移除.py后缀）
        location=file_path
    )

    # 2️⃣ 根据规范创建模块对象
    module = importlib.util.module_from_spec(spec)

    # 3️⃣ 执行模块代码（核心步骤）
    spec.loader.exec_module(module)

    # 4️⃣ 可选：调用模块的main函数
    if hasattr(module, 'main'):
        module.main()  # 若模块定义了main()则执行