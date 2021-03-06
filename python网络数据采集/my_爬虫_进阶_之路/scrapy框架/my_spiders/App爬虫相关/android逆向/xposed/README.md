# xposed
Xposed Framework 为来自国外XDA论坛（forum.xda-developers.com）的rovo89自行开发的一个开源的安卓系统框架。

Xposed框架的原理是修改系统文件，替换了/system/bin/app_process可执行文件，在启动Zygote时加载额外的jar文件（/data/data/de.robv.android.xposed.installer/bin/XposedBridge.jar），并执行一些初始化操作(执行XposedBridge的main方法)。然后我们就可以在这个Zygote上下文中进行某些hook操作。

Xposed Installer框架中真正起作用的是对方法的Hook和Replace。在Android系统启动的时候，Zygote进程加载XposedBridge.jar，将所有需要替换的Method通过JNI方法hookMethodNative指向Native方法xposedCallHandler，这个方法再通过调用handleHookedMethod这个Java方法来调用被劫持的方法转入Hook逻辑。

上面提到的hookMethodNative是XposedBridge.jar中的私有的本地方法，它将一个方法对象作为传入参数并修改Dalvik虚拟机中对于该方法的定义，把该方法的类型改变为Native并将其实现指向另外一个B方法。

换言之，当调用那个被Hook的A方法时，其实调用的是B方法，调用者是不知道的。在hookMethodNative的实现中，会调用XposedBridge.jar中的handleHookedMethod这个方法来传递参数。handleHookedMethod这个方法类似于一个统一调度的Dispatch例程，其对应的底层的C++函数是xposedCallHandler。而handleHookedMethod实现里面会根据一个全局结构hookedMethodCallbacks来选择相应的Hook函数并调用他们的before和after函数，当多模块同时Hook一个方法的时候Xposed会自动根据Module的优先级来排序。

调用顺序如下：A.before -> B.before -> original method -> B.after -> A.after。

![](https://i.loli.net/2019/01/12/5c394e63ca2b4.png)

[github](https://github.com/rovo89/Xposed)

[download](https://repo.xposed.info/module/de.robv.android.xposed.installer)

## download
[安装过程](https://blog.csdn.net/fuchaosz/article/details/53143216)

XposedInstaller_*.apk from this thread: Must be installed to manage installed modules, the framework won't work without it.

xposed*.zip from https://dl-xda.xposed.info/framework/: Must be flashed with a custom recovery (e.g. TWRP) to install the framework.

- SDK21 is Android 5.0 (Lollipop), 
- SDK22 is Android 5.1 (also Lollipop) 
- SDK23 is Android 6.0 (Marshmallow).
- SDK24 is Android 7.0 
- SDK25 is Android 7.1.
- SDK26 is Android 8.0 and SDK27 is Android 8.1.

I only support the latest Xposed version per Android release!

xposed-uninstaller*.zip from https://dl-xda.xposed.info/framework/: Can be flashed with a custom recovery (e.g. TWRP) to uninstall the framework.

The small .asc files are GPG signatures of the .zip files. You can verify them against this key (fingerprint: 0DC8 2B3E B1C4 6D48 33B4 C434 E82F 0871 7235 F333). That's actually the master key, the files are signed with subkey 852109AA.

# VirtualXposed(推荐使用)
无需root的xposed

[github](https://github.com/android-hacker/VirtualXposed)

## 安装
从[发布页面](https://github.com/android-hacker/VirtualXposed/releases)下载最新的APK ，并将其安装在您的Android设备上。

### 安装APP和Xposed模块
打开VirtualXposed，单击主页底部的抽屉按钮（或长按屏幕），将所需的APP和Xposed模块添加到VirtualXposed的虚拟环境中。

注意：所有操作（Xposed Module，APP的安装）必须在VirtualXposed中完成，否则安装的Xposed模块将不会生效。

例如，如果您在系统上安装YouTube应用程序（手机的原始系统，而不是VirtualXposed），然后在VirtualXposed中安装YouTube AdAway（YouTube Xposed模块）; 

或者您在VirtualXposed中安装YouTube，并在原始系统上安装YouTube AdAway; 或者两者都安装在原始系统上，这三种情况都不会起作用！

将应用程序或Xposed模块安装到VirtualXposed有三种方法：

1. 从原始系统克隆已安装的应用程序。（单击主页底部的“按钮”，然后单击“添加应用程序”，第一页显示已安装应用程序的列表。）
2. 通过APK文件安装。（单击主页底部的按钮，然后单击添加应用程序，第二页显示在SD卡中找到的APK）
3. 通过外部文件选择器安装。（单击主页底部的按钮，然后单击添加应用程序，使用浮动操作按钮选择要安装的APK文件）

对于Xposed Module，您也可以从Xposed Installer安装它。

#### 激活Xposed模块
在VirtualXposed中打开Xposed Installer，转到模块片段，检查要使用的模块：

#### 重启
您只需重启VirtualXposed，无需重启手机 ; 只需单击VirtualXposed主页中的Settings，单击Reboot按钮，VirtualXposed将立即重启。

## 基于xposed开发

注意修改的是app/build.gradle配置里面的配置
```bash
repositories {
    jcenter();
}

dependencies {
    provided 'de.robv.android.xposed:api:82'
    provided 'de.robv.android.xposed:api:82:sources'
}
```
[blog1](https://blog.csdn.net/niubitianping/article/details/52571438)

[blog2](https://blog.csdn.net/yzzst/article/details/47659479)

## simple use
```java
package com.example.fzxposedhook81;

import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

/*
* 确保禁用Instant Run（File -> Settings -> Build, Execution, Deployment -> Instant Run）
* 否则你的类不会直接包含在APK中，导致HOOK失败！！！
*
* 注意:
* 1. XposedBridgeApi.jar放入lib(注意不是libs)后, 必须Add As Library! 再修改app下面的 build.gradle把 XposedBridgeApi.jar的implementation换成compileOnly
*   (估计Xposed作者在其框架内部也使用了BridgeApi，使用provided即(compileOnly)依赖避免重复引用；)
*   (不进行上诉操作, loadPackageParam.processName会报java.lang.NullPointreException, 无法进行后续hook)
* */

/*
* 用法:
* Xposed调用FZXposedHook插件
* assets设置为com.example.fzxposedhook81.FZXposedHook
* */

public class FZXposedHook implements IXposedHookLoadPackage {
    @Override
    public void handleLoadPackage(XC_LoadPackage.LoadPackageParam loadPackageParam) throws Throwable {
        String hook_package_name = "com.example.fzxposedhook81";
        XposedBridge.log("fz start hooking package...");
        XposedBridge.log("被加载的process_name:" + loadPackageParam.appInfo.processName);
        XposedBridge.log("@@@被加载的包名:" + loadPackageParam.appInfo.packageName);

        if (loadPackageParam.packageName.equals(hook_package_name)) {
            // equals 判断对象是否相等
            XposedBridge.log("找到该包!!");
//            法1:
//             loadPackageParam.classLoader报NullPointerException
            Class clazz = loadPackageParam.classLoader.loadClass(hook_package_name + ".MainActivity");
//            法2:
//             有些动态加载的类，你用默认的 loadPackageParam.classLoader 怎么都拦截不到，这是正常的，因为它就不在这个 classloader 里
//             但可曲线救国，先 hook 动态加载的类在系统中的父类，通过这个父类找到真正的 classloader，再用这个真正的 classloader 去 hook动态加载的类。
//             拦截onCreate方法，得到 Fragment, 根据当前动态加载的 fragment 去获取它真正的 classloader
//            Class clazz = XposedHelpers.findClass("android.support.v4.app.Fragment", loadPackageParam.classLoader);

            XposedHelpers.findAndHookMethod(clazz, "toast_message", new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                    super.beforeHookedMethod(param);
                }

                @Override
                protected void afterHookedMethod(MethodHookParam param) throws Throwable {
//                    super.afterHookedMethod(param);
                    Class c_name = param.thisObject.getClass();
                    XposedBridge.log("class_name:" + c_name.getName());
                    param.setResult("你已被劫持!");
                }
            });
            XposedBridge.log("别看了, 老子已成功hook!");
        } else {
            XposedBridge.log("未找到package_name:" + hook_package_name);
        }
    }
}
```

## 注意点
```android
/*
* 确保禁用Instant Run（File -> Settings -> Build, Execution, Deployment -> Instant Run）
* 否则你的类不会直接包含在APK中，导致HOOK失败！！！
*
* 注意:
* 1. XposedBridgeApi.jar放入lib(注意不是libs)后, 必须Add As Library! 再修改app下面的 build.gradle把 XposedBridgeApi.jar的implementation换成compileOnly
*   (估计Xposed作者在其框架内部也使用了BridgeApi，使用provided即(compileOnly)依赖避免重复引用；)
*   (不进行上诉操作, loadPackageParam.processName会报java.lang.NullPointreException, 无法进行后续hook)
* */

/*
* 用法:
* Xposed调用FZXposedHook插件
* assets设置为com.example.fzxposedhook81.FZXposedHook
* */
```