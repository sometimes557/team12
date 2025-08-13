import os
cmd='python ymx_get_id.py'
result = os.system(cmd)
if result == 0:
    print("ymx_get_id.py 运行成功")
else:
    print(f"ymx_get_id.py 运行失败，错误代码: {result}")
cmd='python ymx_pac.py'
result = os.system(cmd)
if result == 0:
    print("ymx_pac.py 运行成功")
else:
    print(f"ymx_pac.py 运行失败，错误代码: {result}")
cmd='python main.py'
result = os.system(cmd)
if result == 0:
    print("main.py 运行成功")
else:
    print(f"main.py 运行失败，错误代码: {result}")