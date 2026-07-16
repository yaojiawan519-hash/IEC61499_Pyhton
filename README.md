### 项目简介 
我们尝试使用Python开发一个极简IEC61499 运行时，主要目的是为AI Code 构筑一整套模型（也可以说是IEC61499 本体论），在这个平台上AI Code 可以自动化生成功能块，和功能能块网络（应用）。
初步的实验表明，在这样的模型下，AI 能够迅速，准确地生成和测试符合规范的功能块代码。使我们看到，将程序分解成为规范的小型模块化结构对于AI Code 是十分有益的，每个功能块完成单一的功能。便于生成和调测，也利于人类看懂和审查。
这个Python 的IEC61499 运行时与我们过去编写的C++ 代码也有很大的区别。这次实现了完全对象化设计。将运行时过去的功能，诸如读取数据，写入数据，检索事件队列，建立功能块类型实例这些功能全部写入功能块和运行时的类中。程序架构十分简单。
### 几种功能块的实现 
## 基本功能块 Basic Function Block (BFB)
基本功能块是一类同步计算的功能块，核心是ECC 状态机和Action 构成。ECC 在EventTrigger 中实现，Action 作为功能块类的内部函数。  
## 复合功能块Composite Function Block (CFB)
这是有由多个功能块通过功能块网络实现的功能块。实现方式也做了简化，将复合功能块也加入了内部的功能块字典中，将复合功能块的事件/数据连接也加入连接表中。复合功能块和他内部的功能块一样处理。唯一的区别在于数据传递和事件触发分为复合功能块内和外。复合功能块的运行简化。
## 服务功能 Service Function Block (SFB)
这是与外部资源关联的功能块，大多数是异步操作的方式运行。在这个运行时中，我采纳了Python 的Thread 线程结构。

## OPCUA Server
在runtime 中，建立一个OPCUA Server 的实例，将所有的功能块都转换成OPCUA 的Object ，事件和数据是该对象的变量（Variable）可以通过OPCUA Client访问
## Status Watch 线程
在runtime 中，建立了一个Status Watch 线程，定时地更新 OPCUA 信息模型
## 功能块网络图的绘制
使用 ELK（Eclipse Layout Kernel）的python 工具生成，并且以SVG 图形输出到本地 outputs 目录中
## 导出 4diac fbt 文件
功能块模型中添加了 ExportXML 方法，导出模型的4diac XML 格式（fbt）到outputs 目录中。
## 运行
python main.py
## 运行复合功能块
python Blink.py

## 结束语 
总而言之，AI Code 工程中，模块的结构尽可能规范和清晰，有助于AI 的理解和生成。多一点规范，少一点灵活性。
