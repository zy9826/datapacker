<!-- title:DataPacker通用造数软件使用说明 -->

- [命令行使用说明](#命令行使用说明)
- [配置文件说明](#配置文件说明)
  - [GlobalSavePath](#globalsavepath)
  - [LoadScript](#loadscript)
  - [Package和Fields](#package和fields)
- [处理节点的额外属性说明](#处理节点的额外属性说明)
  - [FillValue](#fillvalue)
  - [变量使用](#变量使用)
  - [DefineVariable](#definevariable)
  - [ExecScript](#execscript)
  - [FillPyEval](#fillpyeval)
  - [FillVariable](#fillvariable)
  - [FillArray](#fillarray)
  - [FillFile](#fillfile)
  - [FillPackage](#fillpackage)
  - [FillSequence](#fillsequence)
  - [CheckSum\*](#checksum)
  - [CrcSum](#crcsum)
  - [CCheckSum](#cchecksum)
- [配置文件编写流程](#配置文件编写流程)
- [Python/C扩展](#pythonc扩展)
  - [Python扩展](#python扩展)
  - [C扩展](#c扩展)


DataPacker是一款通用造数软件，以配置文件驱动的命令行程序，没有图形界面。   
它支持嵌套多层格式，支持定义变量和调用Python脚本或者C语言扩展，支持输入文件数据源并使用生成器对文件进行预处理，支持存储节点自定义满足多样的存盘需求。   
通过修改配置文件、Python脚本扩展和C扩展可以实现绝大部分数据打包格式，而无需修改主程序。 


# 命令行使用说明
DataPacker是命令行程序，没有图形界面，输入datapacker.exe -h可查看帮助信息：
``` bash
datapacker.exe -h
usage: main.py [-h] [-i] [-c CONFIG_DIR] [-n CONFIG_NUM] [-t TEST_FLAG]

options:
  -h, --help            show this help message and exit
  -i, --interactive     交互模式, 需要输入参数时使用
  -c CONFIG_DIR, --config_dir CONFIG_DIR
                        配置文件路径
  -n CONFIG_NUM, --config_num CONFIG_NUM
                        配置文件序号
  -t TEST_FLAG, --test_flag TEST_FLAG
                        测试模式, -t n:开启测试模式, 显示n个最耗时函数, 用于分析耗时
```
datapacker会查找配置文件，每类数据打包格式的配置文件和脚本扩展等文件都必须放在同一个文件夹中，主配置文件必须命名为congig.xml，其他文件可自定义命名。每个文件夹作为一种方案，后文统称为方案目录。  
datapacker有**两种运行模式**，一种交互模式，另一种是非交互模式，通过-i参数指定。交互模式时可通过控制台输入参数，非交互模式时要求所有参数必须通过配置文件完成定义。
datapacker命令行加载方案目录有三种使用方式：
1. 直接运行exe：程序会查找当前路径下的config目录，将其子目录作为方案目录打印并编号，用户输入序号选择方案执行。
2. 使用-n指定配置文件编号，文件编号和方法1的编号相同，此方法使用的方案也在config目录下。
3. 使用-c指定配置文件路径，可以任意指定路径或xml文件名，不一定在config目录下。可拖动文件到控制台输入。


# 配置文件说明
配置文件格式如下，根节点下有三种子节点：GlobalSavePath，LoadScript和Package。   
Packeage用于定于包格式，有两种子节点Fields(定义具体的包格式和处理节点)和SaveNode(定义存储方式)，Fields中还有子节点Field。    
配置文件形式如下：   
``` xml
<?xml version="1.0" encoding="utf-8"?>
<config tips="包格式定义">
    <GlobalSavePath save_path="C:/datalog/" config_named="" time_named=""/>
    <LoadScript script_file="CustomScript.py"/>
    <Package>
        <Fields name="FPGA重构格式" max_size="246" fill_with="0xff" save_flag="1">
            <Field name="包识别" offset="0" size="2" class="FillValue" value="0x1ACF"/>
            <Field name="数据类型" offset="2" size="2" class="FillValue" value="0x000C" input="combo_box" opt_value="0x000B;0x000C;0x000D;0x000E;0x000F" opt_text="微波FPGA;微波CPU;光学头1;光学头2;协同终端"/>
            <vField name="执行脚本1" class="ExecScript" script_file="t0001.py"/>
            <Field name="FLASH块起始地址" offset="4" size="2" class="FillVariable" var_name="blk_addr"/>
            <Field name="FLASH页起始地址" offset="6" size="1" class="FillVariable" var_name="page_addr"/>
            <Field name="分割包计数" offset="7" size="1" class="FillVariable" var_name="page_cnt"/>
            <Field name="有效数据长度" offset="8" size="2" value="0x80" class="FillValue"/>
            <Field name="有效数据" offset="10" size="128" class="FillFile" filename="data/config_236_10241.dat" input="file_input" priority="10" generator="generator:Fill16Gen"/>
            <Field name="和校验" offset="138" size="2" class="CCheckSum" ck_func="isosum" ck_start="0" ck_size="138"/>
            <Field name="填充文件" offset="140" size="100" class="FillCustom2"/>
            <!-- 局部变量表 -->
            <vField name="地址计数" var_name="addr_cnt" value="0" class="DefineVariable"/>
            <vField name="块地址" var_name="blk_addr" value="0" class="DefineVariable"/>
            <vField name="页地址" var_name="page_addr" value="0" class="DefineVariable"/>
            <vField name="页地址计数" var_name="page_cnt" value="0" class="DefineVariable"/>
        </Fields>
    </Package>
    <Package>
        <Fields name="八院FPGA重构格式" max_size="256" save_flag="1" fill_with="0x5A" content="14C0 C000 00F9">
            <Field name="包计数" offset="2" size="2" class="FillPyEval" eval="int(0xC000|_cur_pkg).to_bytes(2,byteorder='big')"/>
            <Field name="功能识别" offset="6" size="2" value="0x000B" class="FillValue" input="line_edit"/>
            <Field name="数据区" offset="8" size="246" class="FillPackage" pkg_name="FPGA重构格式"/>
            <Field name="校验" offset="254" size="2" class="CCheckSum" ck_func="isosum" ck_start="0" ck_size="254"/>
        </Fields>
    </Package>
</config>
```
**注意，配置中有大量的bool类型属性，bool属性的输入规则统一为：属性值不为空为True，属性值为空表示False，无此属性时可能为False或者默认值**


## GlobalSavePath
GlobalSavePath节点用于定义全局存储路径，节点未定义时使用当前路径的output目录。支持以下属性
- config_named：bool值，是否创建输出方案文件夹
- time_named：bool值，是否创建输出时间文件夹


## LoadScript
LoadScript用于加载Python脚本扩展，支持以下属性：
- script_file：加载自定义的处理节点脚本文件字。使用相对路径，指定的文件必须位于方案目录下，也就是和config.xml同级目录。   
  项目使用reflector机制，可通过配置中的字符串构建处理节点类，所有继承ProcessorBase的子类都拥有此能力，因此指定的脚本文件中的类继承自ProcessorBase才能在配置文件中使用。


## Package和Fields
Package，包括包格式定义，处理节点定义和存储节点定义。它拥有两个子节点：Fields和SaveNode，其中Fields是用来定义包格式和处理节点，SaveNode是用于定义存储类。支持以下属性：
- save_flag：bool值，默认保存节点标志。默认保存节点仅支持存储为dat文件，通过save_flag开关。可通过SaveNode节点支持其他自定义存储节点。

Fields节点的属性有：name，max_size，fill_with，content。这四种属性和遥控遥测配置含义相同。
Fields节点有两种子节点：Field和vField。两种节点都需要通过class属性指定处理节点类，区别在于Field时用于定于数据格式的节点必须定义offset和size属性，而vField只用于定义处理节点，无需offset和size。   
下表介绍了所有处理节点的通用属性：
| class名称      | 功能                   | tag    | 默认fixed | 默认priority | input               | 额外属性                                    |
| :------------- | :--------------------- | :----- | :-------- | :----------- | :------------------ | :------------------------------------------ |
| FillValue      | 填充整型值             | Field  | True      | 0            | combo_box,line_edit | value                                       |
| FillPyEval     | 填充脚本返回值         | Field  | False     | 0            | 否                  | eval                                        |
| ExecScript     | 执行脚本               | vField | False     | 0            | 否                  | script_file                                 |
| DefineVariable | 定义变量               | vField | True      | 0            | combo_box,line_edit | var_name,value                              |
| FillVariable   | 填充变量               | Field  | False     | 0            | 否                  | var_name                                    |
| FillArray      | 填充数组               | Field  | True      | 0            | line_edit           | value                                       |
| FillFile       | 填充文件(数据源)       | Field  | True      | 99           | file_input          | filename,fill_with,generator                |
| FillPackage    | 填充其他包格式(数据源) | Field  | False     | 99           | 否                  | pkg_name                                    |
| FillSequence   | 填充序列(数据源)       | Field  | False     | 99           | 是,自定义输入       | seq_type,seq_cnt                            |
| CheckSum*      | 校验类                 | Field  | False     | -99          | 否                  | ck_start,ck_size                            |
| CrcSum         | Crc校验                | Field  | False     | -99          | 否                  | ck_start,ck_size,crc_type                   |
| CCheckSum      | C扩展校验类            | Field  | False     | -99          | 否                  | ck_start,ck_size,lib_file,ck_func,byteorder |

上表只介绍了部分通用属性，还有部分通用属性并未列出，由下文来介绍并进行详细说明。
1. name：节点名称。所有节点都必须定义，即使是无实际含义的vField，可以方便排查问题。
2. class：处理节点类名称。可为空仅作占位，此时使用Fileds>fill_with填充。
3. offset和size：属性含义和遥控遥测配置相同，但此处不支持mask属性。仅Field节点支持，vField节点无需定义。
4. fixed：bool值，fixed属性表明当前处理节点是固定参数或可变参数，每种处理节点都有默认值（见上表），可通过配置修改重新指定。固定参数程序只执行一次，可变参数节点按priority排序后每组一帧按顺序执行一次。
5. priority：整形值，优先级仅fixed=False时有效。程序会根据优先级从大到小排序处理节点，普通节点默认优先级0，数据源节点默认优先级99，校验节点（通常最后计算）默认优先级-99。
6. input：输入类型包括combo_box,line_edit和file_input三种，每种处理节点的输入类型见上表。   
   combo_box类型和遥控遥测一样，有额外的opt_value和opt_text属性；   
   file_input只支持FillFile节点，可将文件拖入命令行界面快捷输入；   
   line_edit支持FillValue，DefineVariable和FillArray三种节点，FillValue和DefineVariable仅支持输入整形变量，FillArray仅支持输入十六进制字符数组。
7. 额外属性由每个节点在下文单独介绍。


# 处理节点的额外属性说明
## FillValue
FillValue通常作为填充固定值（比如帧头之类的）。支持以下属性：
- value：填充的固定值。只支持整形输入，可输入十进制或者带0x的十六进制。
- input：可选combo_box和line_edit。


## 变量使用
接下来介绍的DefineVariable，ExecScript，FillPyEval和FillVariable这四个处理节点中都会用到变量，此处提前介绍变量的使用。   
为了方便扩展，满足组帧时的变化数据要求，程序支持通过DefineVariab节点定义变量，可通过ExecScript节点修改变量，可通过FillPyEval和FillVairab节点使用变量。   
除了自定义的变量，程序中定义了两个全局变量_max_pkg和_cur_pkg，和两个局部变量_pkg_data和_dat_len。全局变量是所有包(Package节点)中都可访问的，而局部变量的作用域只在包内部，通过配置文件定义的变量也属于局部变量。   
ExecScript修改变量可影响到程序内部，而FillPyEval虽然也可修改使用和修改变量值，但不能影响程序内部值，因为两者调用的作用域不同。   
顾名思义，下面是四个变量的含义：   
- _max_pkg：最大包数量，若有多个数据源以最小的那个为准
- _cur_pkg：当前包计数，从0开始计数，通常可用于填充帧计数
- _pkg_data：当前包数据，外部函数可拿到当前包的完整数据，请确认offset和size值确保只修改与当前处理节点匹配的部分。也可用于计算校验时访问全部数据
- _dat_len：当前帧的数据源长度，由数据源处理节点负责更新此变量。


## DefineVariable
DefineVariable用于定义变量，可在ExecScript中修改，可在FillPyEval和FillVariable中使用。支持以下属性：   
- var_name：定义变量名称，对于程序内部来说本质是字符串，无命名要求，但建议使用通用的变量命名规则。
- value：变量初始值，仅支持整形。   
- input：支持combo_box和line_edit。   
例，`<vField name="地址计数" var_name="addr_cnt" value="0" class="DefineVariable"/>`


## ExecScript
ExecScript支持调用脚本文件片段，通常用于修改配置中定义的变量。支持以下属性:   
- script_file：指定脚本文件名，只需要指定文件名称，并且脚本文件必须位于方案目录下。   
例，`<vField name="执行脚本1" class="ExecScript" script_file="t0001.py"/>`。


## FillPyEval
FillPyEval可调用脚本扩展，需要定义eval属性，和遥控遥测的eval功能类似，FillPyEval会加载方案目录下的py_eval.py文件，调用其中的pyStr2Bytes函数执行eval定义。支持以下属性：   
- eval：调用表达式字符串。

FillPyEval可以访问配置文件中定义局部变量或者全局变量，虽然方便使用但每次调用都需要更新全局变量表，而且每次执行都调用两次eval函数，性能差耗时较长，建议尽量少使用。   
并且不同于遥控遥测的eval，它对于返回值有2点要求：**1是必须返回bytearray类型，2是返回的长度必须和定义的size属性相等**。   
程序内部会检查返回值，不满足上述条件时会抛出异常提示。使用示例如下：   
- 表达式调用（最高2bit为11b的帧计数）：
`eval="int(0xC000|_cur_pkg).to_bytes(2,byteorder='big')"`
- 函数调用（使用FillPyEval计算校验）：
``` xml
eval="add8bsum(0,138)"
```
``` python
def add8bsum(ck_start, ck_size):
    sum = 0
    for i in range(ck_start, ck_start + ck_size):
        sum = sum + _pkg_data[i]

    val = sum & 0xFFFF
    return int(val).to_bytes(2, byteorder="big")

def pyStr2Bytes(exp_str, builtin_globals, builtin_locals):
    try:
        ggg = globals()
        ggg.update(builtin_globals)
        ggg.update(builtin_locals)
        ret = eval(exp_str, ggg)
        return ret
    except Exception as e:
        raise e
```


## FillVariable
FillVariable可使用已有的变量填充数据帧中的字段。支持以下属性：
- var_name：指定需要填充的变量名，必须是已存在的变量，填充时会做存在性检查，填充的变量值默认都会转换为大端。
- byteorder：可选["little" | "big"]，默认big

## FillArray
FillArray用于使用十六进制字符串填充数组。支持以下属性：   
- value：填写十六进制字符串，不带0x。 
- input：支持line_edit输入十六进制字符串

## FillFile
FillFile用于填充文件，有两种使用方式：1是当fixed=false时作为数据源；2是当fixed=true是作为填充文件，可作为FillArray的补充。支持以下属性：   
- filename，指定输入文件的全局路径，或者相对路径。使用相对路径时会以方案目录，exe目录的顺序查找文件。
- fill_with，当文件不足指定长度时的填充值。
- generator，指定文件生成器（基于Python生成器实现），用于对文件进行预处理。生成器扩展文件必须放在方案目录下，输入形式为`模块名:生成器类名`，注意模块名相当于不带后缀的文件名，例`generator:FillTxtFile`。   
- input，只支持file_input方法。输入文件路径，可将文件拖动到命令行窗口输入。

生成器简而言之就是必须使用关键字`yield`返回，下次调用时会接着`yield`下一条语句执行，而不是从函数开始执行，详细概念见python文档。   
增加生成器的作用是为了满足对文件进行预处理的需求，比如输入文本文件输出bin文件，比如文件帧数填充到16的整数倍等需求。      
生成器有基类，位于backend.ProcessorBase.GeneratorBase，基类定义了对生成器的基础要求如下，但并非强制要求生成器必须继承基类，满足基础要求即可被datapacker调用。
1. 实现__iter__方法并返回生成器，返回值是bytearray
2. 构造函数接受filename和size两个参数
3. 计算出最大包数max_pkg属性
4. 上报错误请抛出异常
文件帧数填充到16整数倍的示例代码如下：
``` python
import os


class Fill16Gen:
    def __init__(self, filename: str, size: int):
        self.size = size
        self.cur_pkg = 0
        self.max_pkg = 0

        self.ifd = open(filename, "rb")
        if self.ifd is None:
            raise RuntimeError(f"file open failed: {filename}")

        file_sz = os.path.getsize(filename)
        # 计算max_pkg
        self.max_pkg = (file_sz + self.size - 1) // self.size
        self.max_pkg = (self.max_pkg + 15) // 16 * 16  # 必须是16的整数倍
        if self.max_pkg <= 0:
            raise RuntimeError(f"file size invalid: {filename} {file_sz}")

    # 实现__iter__
    def __iter__(self):
        temp = bytearray(self.size)
        read_buf = bytearray(self.size)
        while self.cur_pkg < self.max_pkg:
            read_len = self.ifd.readinto(read_buf)
            if read_len > 0:
                yield read_buf
            else:
                yield temp
            self.cur_pkg += 1
```

## FillPackage 
FillPackage用于获取其他包数据作为数据源。有两种使用方式：1是当fixed=false时作为数据源；2是当fixed=true时作为填充文件。支持以下属性：   
- pkg_name，指定源包名称。加载时做存在性检查，因此被调用的包必须先于当前包定义。

## FillSequence
FillSequence收录了常用的填充序列，可做为数据源。以下表格是所有支持的序列：
| 序号 | 名称           | fixed |
| :--- | :------------- | :---- |
| 0    | 固定数         | True  |
| 1    | 8bit递增码     | True  |
| 2    | 16bit递增码    | True  |
| 3    | 32bit递增码    | True  |
| 4    | 8bit帧间递增码 | False |
| 5    | 8bit随机码     | False |
- seq_type，输入上表中的序号选择序列类型。当序号为0时，支持额外的fixed_value属性，输入固定值参数。
- seq_max_pkg，表示序列最大包数。
- 支持输入，但是自定义的输入逻辑，不需要input属性定义，seq_type和seq_max_pkg都可以通过输入获取。

## CheckSum*   
CheckSum*校验类，此处是指所有python实现的校验类，包括XorSum16b，Add8bSum，Add16bSum，IsoSum和CrcSum，具体实现参见源码。python实现的校验类性能较弱不建议使用，建议使用C扩展的校验类CCheckSum。支持以下属性：
- ck_start：校验起始位置，从0开始的下标。
- ck_end：校验数据长度。

## CrcSum
CrcSum用于计算Crc校验，它虽是python使用，但内部使用的是基于C实现的libscrc库，性能强校验快，并且支持所有crc校验方式，推荐使用。它支持以下属性：
- ck_start：校验起始位置，从0开始的下标。
- ck_end：校验数据长度。
- crc_type：指定crc校验类型字符串，所有crc校验类型参考下列资料。
- byteorder：可选["little" | "big"]，默认big

libscrc参考链接：[PyPI](https://pypi.org/project/libscrc/) [Github](https://github.com/hex-in/libscrc)   
libscrc支持的crc类型摘录：   
libscrc is a library for calculating CRC3 CRC4 CRC5 CRC6 CRC7 CRC8 CRC16 CRC24 CRC32 CRC64 CRC82.

|   CRCx    |    CRC8    |   CRC16    |   CRC24    |     CRC32     |  CRC64  |
| :-------: | :--------: | :--------: | :--------: | :-----------: | :-----: |
| CRC3-GSM  |   INTEL    |   MODBUS   |    BLE     |      FSC      | GO-ISO  |
| CRC3-ROHC |    BCC     |    IBM     |  OPENPGP   |     CRC32     | ECMA182 |
| CRC4-ITU  |    LRC     |   XMODEM   |   LTE-A    |     MPEG2     |   WE    |
| CRC5-ITU  |   MAXIM8   |   CCITT    |   LTE-B    |    ADLER32    |  XZ64   |
| CRC5-EPC  |    ROHC    |   KERMIT   |    OS9     |  FLETCHER32   |         |
| CRC5-USB  |    ITU8    |  MCRF4XX   | FLEXRAY-A  |     POSIX     |         |
| CRC6-ITU  |    CRC8    |    SICK    | FLEXRAY-B  |     BZIP2     |         |
| CRC6-GSM  |    SUM8    |    DNP     | INTERLAKEN |    JAMCRC     |         |
| CRC6-DARC | FLETCHER8  |    X25     |   CRC24    |    AUTOSAR    |         |
|   CRC7    |   SMBUS    |    USB     |            |   C / ISCSI   |         |
| CRC7-MMC  |  AUTOSAR   |  MAXIM16   |            | D / BASE91-D  |         |
| CRC7-UMTS |    LTE     | DECT(R/X)  |            |   Q / AIXM    |         |
| CRC7-ROHC | SAE-J1850  |  TCP/UDP   |            |     XFER      |         |
|           |   I-CODE   |  CDMA2000  |            |     CKSUM     |         |
|   CAN15   |   GSM-A    | FLETCHER16 |            |     XZ32      |         |
|   CAN17   |   NRSC-5   |   EPC16    |            |     AAL5      |         |
|   CAN21   |   WCDMA    |  PROFIBUS  |            |   ISO-HDLC    |         |
|           | BLUETOOTH  |  BUYPASS   |            |     PKZIP     |         |
| CRC10-ATM |   DVB-S2   |  GENIBUS   |            |     ADCCP     |         |
| CRC13-BBC |    EBU     |   GSM16    |            |     V-42      |         |
|  MPT1327  |    DARC    |   RIELLO   |            |     STM32     |         |
| CDMA2000  |   MIFARE   | OPENSAFETY |            |     ECMXF     |         |
|           |   LIN1.3   |  EN13757   |            |               |         |
|           |   LIN2.x   |    CMS     |            |  CRC30-CDMA   | DARC82  |
|           |    ID8     |            |            | CRC31-PHILIPS |         |
|           |    NMEA    |            |            |               |         |
|           | MODBUS_ASC |            |            |               |         |

CrcSum使用配置：   
`<Field name="CRC校验" offset="894" size="2" class="CrcSum" crc_type="ccitt_false" ck_start="4" ck_size="890"/>`

CrcSum实现代码：
``` python
import libscrc
import ctypes


class CrcSum(CheckSumBase):
    """通用CRC校验和, 依赖libscrc库
    通过crc_type属性指定CRC类型, 默认ccitt_false
    """

    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        super().load(xml_node)

        self.crc_type = xml_node.attrib.get("crc_type", "ccitt_false")
        if not hasattr(libscrc, self.crc_type):
            raise RuntimeError(f"{self.package.name}-{self.name}: crc_type not support: {self.crc_type}")
        self.crc_func = getattr(libscrc, self.crc_type)

    def pack(self, data, /, **kwargs) -> bool:
        crc_val = self.crc_func(data[self.ck_start : self.ck_start + self.ck_size])
        ret = crc_val & ((1 << self.size * 8) - 1)
        data[self.offset : self.offset + self.size] = int(ret).to_bytes(self.size, byteorder="big")
        return True
```

## CCheckSum
CCheckSum是基于C扩展实现的校验类，默认加载cchecksum.dll调用默认实现的C函数库，包括sum8bit，sum16bit，xor16bit，isosum等函数。也可通过lib_file属性指定自定义的函数库。   
为了方便代码实现，要求C校验函数使用统一的函数签名`uint64_t (uint8_t* bytes, int len)`，要求返回值uint64_t, 参数为uint8_t指针,len为字节长度。它支持以下属性：
- ck_start：校验起始位置，从0开始的下标。
- ck_end：校验数据长度。
- lib_file：指定dll路径，使用相对路径，必须位于方案目录下。不指定时使用默认的ccheksum.dll。
- ck_func：指定调用的函数名称。
- byteorder：可选["little" | "big"]，默认big   
使用示例：`<Field name="和校验" offset="138" size="2" class="CCheckSum" ck_func="isosum" ck_start="0" ck_size="138"/>`


# 配置文件编写流程
1. 判断数据文件是否需要预处理，需要预处理则得编写生成器
2. 将数据协议中的字段分为四类：
- 固定字段，通常使用FillValue，FillArray填充
- 变化字段，通常通过定义变量(DefineVariable，ExecScript，FillVairiable，FillPyEval等类)实现，或者通过自定义处理节点扩展实现。
- 参数可选字段，类似固定字段使用FillValue，FilleArray填充，通过input属性指定输入字段
- 校验字段，查看文档的校验类是否满足，不满足可通过Python/C自定义扩展
可按照固定字段，参数可选字段，校验字段，变化字段的顺序编写配置文件，编写完前三种字段后可先生成数据检查下数据是否符合预期，最后在编写调试变化字段参数。   
调试时可先使用小数据量测试，脚本扩展中可使用打印语句调试。   


# Python/C扩展
根据上文中的配置文件介绍可以了解到配置文件中的每一项都对应代码中的一个处理节点类，每个处理节点类都继承自ProcessorBase，包括校验类和存储节点类都继承自它。
ProcessorBase有三个主要的函数，作用如下：
- load：接受一个xml节点，处理该节点所需属性，不满足条件时抛出异常报错
- input：数据函数，根据节点需要可选择性重写。
- pack：接受一帧数据(bytearray类型)，返回bool值，当组包到最后一帧时返回False，通知上层调用退出循环，否则返回True。
**注意**：每个处理节点的pack都接受的完整数据帧，可访问当前帧所有数据。原则上每个节点根据配置的offset和size只修改对应位置的数据，实际上你要一个节点处理多个位置数据也没关系，反而可能更快，但是不通用了。  

## Python扩展
扩展自定义类时必须继承自ProcessBase类，而它在backend.processor.ProcessorBase模块中，所以import语句写法参考下文示例代码第一行。   
类似的继承校验类的import语句：`from backend.processor.CheckSum import CheckSumBase`。
``` python
from backend.processor.ProcessorBase import ProcessorBase
from pathlib import Path


class SaveDualChannel(ProcessorBase):
    def __init__(self):
        super().__init__()
        self.frm_cnt = 0
        self.fd1 = None
        self.fd2 = None

    def __del__(self):
        if self.fd1 is not None:
            self.fd1.close()
        if self.fd2 is not None:
            self.fd2.close()

    def load(self, xml_node):
        self.filename1 = Path(self.package.global_save_path) / (self.package.name + "_通道1.dat")
        self.filename2 = Path(self.package.global_save_path) / (self.package.name + "_通道2.dat")
        self.fd1 = open(self.filename1, "wb")
        self.fd2 = open(self.filename2, "wb")

    def pack(self, data, /, **kwargs) -> bool:
        if self.frm_cnt % 2 == 0:
            self.fd1.write(data)
        else:
            self.fd2.write(data)
        self.frm_cnt += 1
        return True
```


## C扩展
目前使用的C扩展很简单但也能满足绝大多数数需求，将C函数编译成dll库，即可通过ctypes加载dll文件，并通过函数字符换获取函数并调用。   
项目中的clibrary文件夹对应C扩展相关，使用cmake做项目管理，也可以使用其他工具管理项目，编译成dll即可。
以下是将图像数据有8it转换为12bit的C函数扩展，在“微纳-可见图像”中的自定义生成器generator.py中调用，代码如下：
``` cmake
cmake_minimum_required(VERSION 3.20)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

project(csample)


# 生成dll
add_library(csample SHARED csample.c)
target_compile_definitions(csample PRIVATE CSAMPLE_EXPORTS) # 定义导出宏

# 设置动态库的输出目录
set_target_properties(csample PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

file(GLOB allCopyFiles  "${CMAKE_CURRENT_SOURCE_DIR}/*.h")
file(COPY ${allCopyFiles} DESTINATION ${CMAKE_BINARY_DIR}/include)
```

``` c
#ifndef CSAMPLE_H
#define CSAMPLE_H

#include <stdint.h>

#ifdef _WIN32
#ifdef CSAMPLE_EXPORTS
#define CSAMPLE_API __declspec(dllexport)
#else
#define CSAMPLE_API __declspec(dllimport)
#endif
#else
#define CSAMPLE_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

CSAMPLE_API uint64_t lshift4bit(uint8_t* bytes, int len);

#ifdef __cplusplus
}
#endif

#endif  // CSAMPLE_H
```

``` c
#include "csample.h"

uint64_t lshift4bit(uint8_t* bytes, int len)
{
    int times = len / 3;
    for(int i = times - 1; i >= 0; i--)
    {
        int s_ofs = i * 2;
        uint8_t B1 = bytes[s_ofs];
        uint8_t B2 = bytes[s_ofs + 1];

        int d_ofs = i * 3;
        bytes[d_ofs] = B1;
        bytes[d_ofs + 1] = (B2 >> 4) & 0x0F;
        bytes[d_ofs + 2] = (B2 & 0x0F) << 4;
    }
    return len;
}
```

``` python
import os
import ctypes
from pathlib import Path

lib_file = Path(__file__).parent / "csample.dll"
if not lib_file.exists() or not lib_file.is_file():
    raise RuntimeError(f"csample.dll not found: {lib_file}")

csample = ctypes.cdll.LoadLibrary(lib_file)
lshift4bit = csample.lshift4bit
# 以上是加载dll和函数的全部代码，下面大部分是业务逻辑无需关心，只需要关心lshift4bit如何调用

class GenP:
    def __init__(self, filename: str, size: int):
        self.size = size
        self.cur_pkg = 0
        self.max_pkg = 0

        file_sz = os.path.getsize(filename)
        if file_sz % (6144 * 8) != 0 and file_sz > 0:
            raise RuntimeError("P谱段数据长度必须是6144*8的整数倍")

        self.ifd = open(filename, "rb")
        if self.ifd is None:
            raise RuntimeError(f"file open failed: {filename}")

        self.max_pkg = file_sz // 6144
        print(f"P谱段数据长度: {file_sz}, 包数: {self.max_pkg} ")

    def __iter__(self):
        frm8_buf = bytearray(6144 * 8)
        db_len = 6144 // 2 * 3
        db_frm = bytearray(db_len)
        while True:
            mod = self.cur_pkg % 8
            if mod == 0:
                self.ifd.readinto(frm8_buf)

            db_frm[0:6144] = frm8_buf[mod * 6144 : (mod + 1) * 6144]
            lshift4bit(ctypes.pointer(ctypes.c_ubyte.from_buffer(db_frm)), db_len)
            yield db_frm
            self.cur_pkg += 1
            if self.cur_pkg >= self.max_pkg:
                break


class GenB:
    def __init__(self, filename: str, size: int):
        self.size = size
        self.cur_pkg = 0
        self.max_pkg = 0

        file_sz = os.path.getsize(filename)
        if file_sz % (1536 * 8) != 0 and file_sz > 0:
            raise RuntimeError("B谱段数据长度必须是1536*8的整数倍")

        self.ifd = open(filename, "rb")
        if self.ifd is None:
            raise RuntimeError(f"file open failed: {filename}")

        self.max_pkg = file_sz // 1536
        print(f"B谱段数据长度: {file_sz}, 包数: {self.max_pkg} ")

    def __iter__(self):
        frm8_buf = bytearray(1536 * 8)
        db_len = 1536 // 2 * 3
        db_frm = bytearray(db_len)
        while True:
            mod = self.cur_pkg % 8
            if mod == 0:
                self.ifd.readinto(frm8_buf)

            db_frm[0:1536] = frm8_buf[mod * 1536 : (mod + 1) * 1536]
            lshift4bit(ctypes.pointer(ctypes.c_ubyte.from_buffer(db_frm)), db_len)
            yield db_frm
            self.cur_pkg += 1
            if self.cur_pkg >= self.max_pkg:
                break
```

