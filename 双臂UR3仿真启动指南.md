# 双臂 UR3 仿真与路径规划指南

目标：先不连接真实机械臂，在 `/home/xiaoai/gzu_ws` 中完成三件事：

1. 看见双臂 UR3 模型。
2. 让 Gazebo 中的双臂按关节轨迹动起来。
3. 用 MoveIt 对 `left_arm`、`right_arm` 或 `both_arm` 做路径规划，并执行到 Gazebo 中的机械臂。

建议学习顺序：

```text
RViz 看模型 -> Gazebo 看物理仿真 -> MoveIt 假执行路径规划 -> Gazebo + MoveIt
```

初学阶段不要一上来就追求抓取。先让双臂“稳定显示、稳定动、稳定规划”，后面再加夹爪、物体和装配任务。

当前稳定方案说明：

```text
Gazebo + MoveIt 联合仿真使用 ur3_dual_gazebo.xacro
```

这个 Gazebo 模型只保留双 UR3 本体，不加载 Robotiq 夹爪物理关节。这样控制器、`/joint_states` 和 TF 更稳定，适合先完成双臂规划和执行。夹爪相关的 SRDF 碰撞忽略项会产生一些 `Link 'xxx_finger' is not known to URDF` 警告，属于已知警告，不影响双臂本体规划。

## 1. 每次新终端先做的事

打开新终端后执行：

```bash
cd /home/xiaoai/gzu_ws
command -v conda >/dev/null 2>&1 && conda deactivate || true
source /opt/ros/noetic/setup.bash
source devel/setup.bash
```

`command -v conda ...` 这一行表示“如果当前机器有 conda，就退出 conda 环境；没有 conda 就跳过”。这样可以避免 conda 的 Qt/Python 库影响 RViz、MoveIt。

## 2. 一键清理旧仿真

如果 RViz、Gazebo、MoveIt 开多了，容易互相干扰。重新开始前可以执行：

```bash
pkill -x rviz || true
pkill -x gzclient || true
pkill -x gzserver || true
pkill -x roslaunch || true
pkill -x rosmaster || true
pkill -x joint_state_publisher || true
pkill -x joint_state_publisher_gui || true
pkill -x robot_state_publisher || true
pkill -x move_group || true
```

然后重新打开一个终端，重新 `source devel/setup.bash`。

## 3. 先确认模型文件

本工作区有两个双臂模型入口：

| 文件 | 用途 | 说明 |
| --- | --- | --- |
| `src/ur_description/urdf/ur3_dual.xacro` | MoveIt 完整模型 | 带双 UR3 和 Robotiq 夹爪 |
| `src/ur_description/urdf/ur3_dual_gazebo.xacro` | RViz 只看模型 / Gazebo / Gazebo+MoveIt | 双 UR3 本体，不带夹爪，显示和控制更稳定 |

不要直接裸运行 `ur3_dual.xacro`，因为它需要 `robot_model:=ur3` 参数。正确方式是通过 launch 启动。

检查 URDF：

```bash
cd /home/xiaoai/gzu_ws
source devel/setup.bash
xacro src/ur_description/urdf/ur3_dual.xacro robot_model:=ur3 > /tmp/ur3_dual.urdf
check_urdf /tmp/ur3_dual.urdf
```

如果看到左右臂链路，例如 `left_arm_upper_arm_link`、`right_arm_upper_arm_link`，说明模型本体是存在的。

## 4. RViz 只看模型

用途：只确认模型、TF、关节滑块，不做路径规划。

这个入口会自动给 RViz 设置 `LIBGL_ALWAYS_SOFTWARE=1`。在 WSLg / Ubuntu 20.04 中，如果不强制软件渲染，可能出现“网格正常、RobotModel 不显示”的情况；你之前能显示的 `demo_gazebo.launch` 也是靠这个环境变量稳定渲染的。

启动：

```bash
cd /home/xiaoai/gzu_ws
source devel/setup.bash
roslaunch ur_description view_ur3_dual.launch
```

正常会打开两个窗口：

1. RViz：显示双臂 UR3 本体。
2. Joint State Publisher GUI：关节滑块。

在滑块窗口拖动关节，RViz 中模型会跟着动。

如果 RViz 看不到机械臂：

1. 左侧 Displays 里确认有 `RobotModel`。
2. `Global Options -> Fixed Frame` 必须是 `world`。
3. `RobotModel -> Robot Description` 必须是 `robot_description`。
4. `RobotModel -> Visual Enabled` 勾选。
5. `RobotModel -> Collision Enabled` 建议先不要勾选，只看视觉模型。
6. 用鼠标滚轮缩放，或者右侧 Views 面板点 `Zero`。

这条命令现在和 Gazebo 联合仿真一样，加载 `ur3_dual_gazebo.xacro`。它只用于确认双 UR3 本体、TF 和关节滑块，夹爪调试请看真实机器人使用手册中的 Robotiq 章节。之前 RViz 看不到，主要原因是旧的 view-only 入口加载了带夹爪的完整模型和碰撞显示，显示不如 Gazebo 专用模型稳定。

如果仍然只看到网格，先完整清理旧进程再启动：

```bash
pkill -x rviz || true
pkill -x roslaunch || true
pkill -x rosmaster || true
pkill -x joint_state_publisher_gui || true
pkill -x robot_state_publisher || true

cd /home/xiaoai/gzu_ws
source devel/setup.bash
roslaunch ur_description view_ur3_dual.launch
```

注意：这个入口只看模型，不带 `MotionPlanning` 面板，也不会启动 Gazebo。要做路径规划并让 Gazebo 同步执行，请用第 10 节的 `demo_gazebo.launch`。

## 5. Gazebo 只看双臂本体

用途：启动物理仿真，让 Gazebo 中出现双臂 UR3。

启动：

```bash
cd /home/xiaoai/gzu_ws
source devel/setup.bash
roslaunch ur_description ur3_dual_gazebo.launch
```

本机已验证会生成：

```text
model_names:
  - ground_plane
  - robot
```

并启动三个控制器：

```text
joint_state_controller
left_arm_joint_traj_controller
right_arm_joint_traj_controller
```

确认 Gazebo 里有模型：

```bash
rosservice call /gazebo/get_world_properties "{}"
```

确认控制器：

```bash
rosservice call /controller_manager/list_controllers "{}"
```

## 6. Gazebo 初始位置

初始关节角写在：

```text
src/ur_description/launch/ur3_dual_gazebo.launch
```

默认启动位姿：

```text
left_arm:  shoulder_pan= 1.2, shoulder_lift=-1.0, elbow=1.4, wrist_1=-1.4, wrist_2=-1.57, wrist_3=0.0
right_arm: shoulder_pan=-1.2, shoulder_lift=-1.0, elbow=1.4, wrist_1=-1.4, wrist_2= 1.57, wrist_3=0.0
```

它通过 `spawn_model` 的 `-J` 参数设置：

```text
-J left_arm_shoulder_pan_joint 1.2
-J right_arm_shoulder_pan_joint -1.2
```

临时修改某个初始角，可以这样启动：

```bash
roslaunch ur_description ur3_dual_gazebo.launch \
  left_shoulder_pan:=0.3 \
  right_shoulder_pan:=-0.3
```

## 7. Gazebo 中让双臂动起来

我已经新增了一个简单脚本：

```text
src/ur_description/scripts/send_ur3_dual_pose.py
```

Gazebo 启动后，另开一个终端执行：

```bash
cd /home/xiaoai/gzu_ws
source devel/setup.bash
rosrun ur_description send_ur3_dual_pose.py --pose home --duration 4
```

可用位姿：

| 位姿 | 命令 |
| --- | --- |
| 默认观察位姿 | `rosrun ur_description send_ur3_dual_pose.py --pose home --duration 4` |
| 左右臂张开 | `rosrun ur_description send_ur3_dual_pose.py --pose ready --duration 3` |
| 收拢姿态 | `rosrun ur_description send_ur3_dual_pose.py --pose folded --duration 4` |

这个脚本不做 MoveIt 规划，只是直接给 Gazebo 控制器发关节轨迹。它适合验证“Gazebo 机械臂能动”。

查看当前关节角：

```bash
rostopic echo -n 1 /joint_states
```

## 8. MoveIt 双臂路径规划

用途：让 MoveIt 对双臂做真正的路径规划。初学建议先用 MoveIt fake execution，不接 Gazebo，稳定、清楚、容易调。

启动 MoveIt + RViz：

```bash
cd /home/xiaoai/gzu_ws
source devel/setup.bash
roslaunch ur3_dual_moveit_config demo.launch
```

RViz 打开后，在 MotionPlanning 面板中：

1. `Planning Group` 选择 `both_arm`。
2. 选择一个目标，或者拖动末端交互标记。
3. 点击 `Plan`。
4. 轨迹没碰撞、看起来合理后，再点 `Execute`。

规划组含义：

| 规划组 | 含义 |
| --- | --- |
| `left_arm` | 只规划左臂 |
| `right_arm` | 只规划右臂 |
| `both_arm` | 左右臂联合规划 |

## 9. 一键运行双臂路径规划 demo

我已经新增 MoveIt 规划脚本：

```text
src/ur3_dual_moveit_config/scripts/plan_both_arms_demo.py
```

第一步，启动 MoveIt：

```bash
cd /home/xiaoai/gzu_ws
source devel/setup.bash
roslaunch ur3_dual_moveit_config demo.launch
```

第二步，另开一个终端运行双臂规划：

```bash
cd /home/xiaoai/gzu_ws
source devel/setup.bash
rosrun ur3_dual_moveit_config plan_both_arms_demo.py
```

它会让 `both_arm` 依次规划并执行：

```text
home -> open -> assemble_ready -> home
```

也可以指定动作序列和速度比例：

```bash
rosrun ur3_dual_moveit_config plan_both_arms_demo.py \
  --poses home open home \
  --velocity-scale 0.2 \
  --acceleration-scale 0.2
```

脚本中的 `home`、`open`、`assemble_ready` 已换成 MoveIt 碰撞检测有效的安全姿态。Gazebo 仿真存在轻微关节抖动，如果执行阶段偶发 `CONTROL_FAILED`，先用 RViz 的 `Plan` 确认规划轨迹，再用第 7 节的控制器脚本验证 Gazebo 运动链路。

如果你想先不打开 RViz，只测试脚本：

```bash
roslaunch ur3_dual_moveit_config demo.launch use_rviz:=false
```

然后另一个终端运行：

```bash
rosrun ur3_dual_moveit_config plan_both_arms_demo.py
```

## 10. Gazebo + MoveIt 联合仿真：Plan 并 Execute

这是现在推荐的主入口。它会同时启动 Gazebo、MoveIt、RViz 和 Gazebo 轨迹控制器，RViz 默认加载带 `MotionPlanning` 面板的配置，可以直接 `Plan` 和 `Execute`。

```bash
cd /home/xiaoai/gzu_ws
source devel/setup.bash
LIBGL_ALWAYS_SOFTWARE=1 roslaunch ur3_dual_moveit_config demo_gazebo.launch
```

如果你的机器 RViz 不闪退，也可以不加 `LIBGL_ALWAYS_SOFTWARE=1`：

```bash
roslaunch ur3_dual_moveit_config demo_gazebo.launch
```

这个模式会同时启动：

1. Gazebo
2. MoveIt `move_group`
3. RViz
4. `left_arm_joint_traj_controller` 和 `right_arm_joint_traj_controller`

当前联合仿真默认使用 `src/ur3_dual_moveit_config/worlds/dual_ur3_no_gravity.world`。这个世界关闭重力，适合先验证 MoveIt 到 Gazebo 的执行链路。启动后会自动发送一次 `home` 姿态，让两只 UR3 进入对称初始状态。

启动时如果看到 `Link 'left_xxx_finger' is not known to URDF`，这是因为 MoveIt 的 SRDF 里保留了 Robotiq 夹爪碰撞忽略项，而当前稳定 Gazebo 模型只保留双 UR3 本体，不加载夹爪。这类警告不影响双臂本体规划和执行。

RViz 打开后，左侧应该能看到：

```text
RobotModel
MotionPlanning
```

如果只看到 `RobotModel`，没有 `MotionPlanning`，说明加载的是只看模型配置。关闭后重新用上面的 `demo_gazebo.launch` 启动，或者显式指定：

```bash
roslaunch ur3_dual_moveit_config demo_gazebo.launch \
  rviz_config:=/home/xiaoai/gzu_ws/src/ur3_dual_moveit_config/launch/moveit.rviz
```

在 RViz 中规划并执行：

1. 展开左下角 `MotionPlanning` 面板。
2. `Planning Group` 先选 `left_arm` 或 `right_arm`，确认单臂能规划。
3. `Goal State` 可以先用 `<random valid>` 或拖动末端交互标记。
4. 点击 `Plan`。
5. 轨迹预览合理后，点击 `Execute`，Gazebo 中机械臂会跟着运动。
6. 单臂正常后，再选 `both_arm` 做双臂联合规划。

注意：`Plan` 只是在 RViz 里生成橙色/半透明的轨迹预览，不会把目标发送给 Gazebo 控制器。只有点击 `Execute` 或 `Plan & Execute`，Gazebo 里的机械臂才会真正运动。

如果你点了 `Execute` 但 Gazebo 没动，先不要反复拖目标点，按下面顺序确认：

```bash
rosservice call /controller_manager/list_controllers "{}"
rosparam get /move_group/controller_list
rostopic echo -n 1 /joint_states
```

`/move_group/controller_list` 里必须是 `left_arm_joint_traj_controller` 和 `right_arm_joint_traj_controller`，不是 fake controller。`/joint_states` 中速度应接近 0，初始关节应接近下面这组对称值：

```text
left:  shoulder_pan= 1.2, shoulder_lift=-1.0, elbow=1.4, wrist_1=-1.4, wrist_2=-1.57, wrist_3=0.0
right: shoulder_pan=-1.2, shoulder_lift=-1.0, elbow=1.4, wrist_1=-1.4, wrist_2= 1.57, wrist_3=0.0
```

如果 `Plan & Execute` 显示 `Failed`，先在终端检查控制器和 action 是否存在：

```bash
rosservice call /controller_manager/list_controllers "{}"
rostopic list | grep follow_joint_trajectory
```

应该能看到：

```text
left_arm_joint_traj_controller
right_arm_joint_traj_controller
/left_arm_joint_traj_controller/follow_joint_trajectory/...
/right_arm_joint_traj_controller/follow_joint_trajectory/...
```

执行前建议把速度调低：

```text
Velocity Scaling = 0.10
Accel. Scaling = 0.10
```

这样 Gazebo 中的动作更慢、更稳。

如果你只想看模型，不需要 `MotionPlanning` 面板，可以启动轻量 RViz 配置：

```bash
roslaunch ur3_dual_moveit_config demo_gazebo.launch \
  rviz_config:=/home/xiaoai/gzu_ws/src/ur3_dual_moveit_config/launch/gazebo_robot_model.rviz
```

这个轻量配置只显示模型，没有路径规划面板。初学阶段如果只想学路径规划，优先用 `demo.launch`；如果只想学 Gazebo 控制，优先用 `ur_description ur3_dual_gazebo.launch`；如果要验证“MoveIt 执行到 Gazebo”，用 `demo_gazebo.launch`。

## 10.1 用脚本验证 Gazebo + MoveIt 执行

启动联合仿真后，另开一个终端：

```bash
cd /home/xiaoai/gzu_ws
source devel/setup.bash
rosrun ur3_dual_moveit_config plan_both_arms_demo.py \
  --poses home open home \
  --velocity-scale 0.1 \
  --acceleration-scale 0.1
```

如果脚本输出 `Plan to ... succeeded`，并且 Gazebo 中机械臂跟随运动，说明 MoveIt 到 Gazebo 控制器链路是通的。

如果 `Plan` 成功但 `Execute` 报错：

```text
CONTROL_FAILED
GOAL_TOLERANCE_VIOLATED
```

通常是 Gazebo 物理仿真里的关节抖动、启动时未回到 `home`，或腕关节角度绕到 `+-2pi` 附近导致，不是 RViz 显示问题。先把速度和加速度比例降到 `0.05` 到 `0.10`，并优先测试单臂 `left_arm` / `right_arm`。确认 Gazebo 控制器本身能动，可以运行：

```bash
rosrun ur_description send_ur3_dual_pose.py --pose ready --duration 5
rosrun ur_description send_ur3_dual_pose.py --pose home --duration 3
```

## 10.2 双臂端托盘 demo

用途：先做“两个 UR3 协同端着一个托盘移动”的教学仿真，不先碰真实夹爪接触物理。

原理：

1. `demo_gazebo.launch` 启动 Gazebo、MoveIt、控制器和 RViz。
2. `carry_tray_demo.py` 用 `/gazebo/spawn_sdf_model` 生成一个蓝色薄托盘。
3. 脚本直接给左右 `JointTrajectoryController` 发送关节轨迹。
4. 机械臂执行轨迹时，脚本用 `/gazebo/set_model_state` 让托盘跟随移动。

启动联合仿真：

```bash
cd /home/xiaoai/gzu_ws
source devel/setup.bash
LIBGL_ALWAYS_SOFTWARE=1 roslaunch ur3_dual_moveit_config demo_gazebo.launch
```

另开终端运行端托盘 demo：

```bash
cd /home/xiaoai/gzu_ws
source devel/setup.bash
rosrun ur3_dual_moveit_config carry_tray_demo.py
```

预期现象：

1. Gazebo 中出现 `dual_ur3_tray` 蓝色托盘。
2. 双臂从 `home` 到 `support`。
3. 双臂移动到 `carry`。
4. 双臂回到 `support` 和 `home`。

注意：这是第一版“协同搬运演示”，托盘只作为 Gazebo 中的可视化模型和同步移动对象，没有加入 MoveIt 碰撞场景，也不走 RRT 规划。托盘不是靠真实摩擦被夹住，而是脚本同步更新托盘位姿。这样做的目的，是先把双臂协同动作、Gazebo 控制器和托盘可视化跑通。真正夹爪抓取需要再加入 Robotiq 物理模型、夹爪控制器、MoveIt 抓取场景和 attach/detach 或 grasp plugin。

## 11. 常见问题

### 11.1 RViz 只有彩色圆环，没有机械臂

彩色圆环是 MoveIt 交互标记。确认 Displays 中有 `RobotModel`，并且：

```text
Fixed Frame = world
Robot Description = robot_description
```

如果是 `view_ur3_dual.launch` 只看模型入口，它已经在 launch 内部强制设置 `LIBGL_ALWAYS_SOFTWARE=1`。如果你手动开 RViz，也要这样启动：

```bash
LIBGL_ALWAYS_SOFTWARE=1 rviz -d /home/xiaoai/gzu_ws/src/ur_description/cfg/view_ur3_dual.rviz
```

### 11.2 `move_group` 找不到

说明 MoveIt 没装全。安装：

```bash
sudo apt update
sudo apt install ros-noetic-moveit ros-noetic-trac-ik-kinematics-plugin
```

### 11.3 `source devel/setup.bash` 权限报错

修复：

```bash
chmod +x /home/xiaoai/gzu_ws/devel/_setup_util.py
source /home/xiaoai/gzu_ws/devel/setup.bash
```

### 11.4 Gazebo 里模型乱动或下坠

联合仿真入口 `ur3_dual_moveit_config demo_gazebo.launch` 已默认使用无重力世界，并且 Gazebo 专用模型的红色基座只保留视觉、不参与碰撞。这样可以避免基座碰撞体把机械臂顶开，导致“蹦跳”或执行失败。

先确认控制器是 running：

```bash
rosservice call /controller_manager/list_controllers "{}"
```

如果控制器没起来，重启：

```bash
pkill -x gzclient || true
pkill -x gzserver || true
pkill -x roslaunch || true
roslaunch ur_description ur3_dual_gazebo.launch
```

### 11.5 MoveIt Plan 失败

常见原因：

1. 目标太远，超过 UR3 工作空间。
2. 左右臂互相碰撞。
3. 起点状态还没更新。
4. 规划时间太短。

处理方式：

1. 先选 `left_arm` 或 `right_arm` 单臂规划。
2. 再选 `both_arm`。
3. 使用较小幅度的目标，不要一步移动太远。
4. 在 Planning 面板里增加 Planning Time。

## 12. 推荐练习路线

第一天：

```bash
roslaunch ur_description view_ur3_dual.launch
```

目标：看懂模型、关节名、TF、滑块。

第二天：

```bash
roslaunch ur_description ur3_dual_gazebo.launch
rosrun ur_description send_ur3_dual_pose.py --pose ready --duration 3
```

目标：看懂 Gazebo 控制器和 `/joint_states`。

第三天：

```bash
roslaunch ur3_dual_moveit_config demo.launch
rosrun ur3_dual_moveit_config plan_both_arms_demo.py
```

目标：完成 `both_arm` 双臂路径规划。

第四天以后：

1. 给桌面、工件、夹具建模型。
2. 做单臂抓取路径。
3. 做左右臂交替运动。
4. 做双臂协同装配。
