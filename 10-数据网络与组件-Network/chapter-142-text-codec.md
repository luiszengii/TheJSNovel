《第 142 次记录: 编码的战争 —— TextDecoder 与 TextEncoder 的真实面目》

---

## PR 评审中的争论

周三下午三点, 会议室的投影仪上显示着一个 Pull Request。

你坐在长桌的一侧, 对面是后端开发小李。气氛有些微妙——你们已经为这个 PR 争论了快二十分钟了。

问题的起因很简单: 小李提交了一个文件上传功能, 需要在前端将用户输入的文本转换成二进制数据, 然后通过 WebSocket 发送给服务器。他的代码是这样写的:

```javascript
function sendText(text) {
    const bytes = [];
    for (let i = 0; i < text.length; i++) {
        bytes.push(text.charCodeAt(i));
    }
    const buffer = new Uint8Array(bytes);
    ws.send(buffer);
}
```

"这代码有什么问题吗?" 小李问, "我测试过了, 英文和数字都能正常传输。"

"问题在于中文和 emoji, " 你指着屏幕说, "你这样只能处理 ASCII 字符。一旦用户输入中文或者表情符号, 数据就会损坏。"

"那应该怎么改?" 小李有些不服气, "我看网上很多例子都是这样写的。"

你正要解释, 旁边的老张插话了: "我记得有个 TextEncoder API 可以处理这个问题, 但我不太确定它和手动转换有什么区别。"

你意识到这是一个很好的机会, 可以让整个团队理解字符编码的底层机制。你打开了本地的测试环境。

---

## 编码的真相

"让我们先看看小李的代码会发生什么, " 你说着, 在控制台输入测试代码:

```javascript
const text = "你好 World 😀";

// 小李的方法
const bytes1 = [];
for (let i = 0; i < text.length; i++) {
    bytes1.push(text.charCodeAt(i));
}
console.log('charCodeAt 结果:', bytes1);
// [20320, 22909, 32, 87, 111, 114, 108, 100, 32, 55357, 56832]

// 转成 Uint8Array
const buffer1 = new Uint8Array(bytes1);
console.log('Uint8Array:', Array.from(buffer1));
// [96, 93, 32, 87, 111, 114, 108, 100, 32, 93, 0]
```

"看到了吗?" 你指着输出结果, "'你好' 两个字的 Unicode 码点是 20320 和 22909, 但 Uint8Array 只能存储 0-255 的值, 所以它们被截断成了 96 和 93。emoji 也是同样的问题。"

小李盯着屏幕, 皱起了眉头: "那数据不就完全错了?"

"对, " 你点头, "而且这个错误是不可逆的。服务器收到的数据已经损坏, 无法还原成原始文本了。"

老张问: "那 TextEncoder 是怎么解决这个问题的?"

你继续演示:

```javascript
// 正确的方法: 使用 TextEncoder
const encoder = new TextEncoder();
const encoded = encoder.encode(text);

console.log('TextEncoder 结果:', Array.from(encoded));
// [228, 189, 160, 229, 165, 189, 32, 87, 111, 114, 108, 100, 32, 240, 159, 152, 128]

console.log('字节长度:', encoded.byteLength);
// 17
```

"TextEncoder 使用 UTF-8 编码, " 你解释, "'你' 被编码成了 3 个字节 [228, 189, 160], '好' 也是 3 个字节 [229, 165, 189]。emoji '😀' 被编码成了 4 个字节 [240, 159, 152, 128]。所有这些字节都在 0-255 范围内, 可以安全地存储在 Uint8Array 中。"

"但这样编码后的数据, 服务器能理解吗?" 小李问。

你打开了解码的示例:

```javascript
// 服务器端解码
const decoder = new TextDecoder();
const decoded = decoder.decode(encoded);

console.log('解码结果:', decoded);
// "你好 World 😀"

console.log('原文对比:', decoded === text);
// true
```

"完美恢复, " 你说, "因为 UTF-8 是一个标准的编码方案。只要编码和解码都使用 UTF-8, 数据就不会丢失。"

老张若有所思: "所以 TextEncoder 和 TextDecoder 就是专门用来在字符串和二进制数据之间转换的?"

"对, " 你确认, "而且它们还有一些额外的功能。"

---

## 编码的边界

小李还有疑问: "如果我的数据不是 UTF-8 呢? 比如后端系统是老的 GBK 编码?"

"好问题, " 你赞许地点头, "TextEncoder 只支持 UTF-8, 这是它的限制。但 TextDecoder 可以解码多种编码格式。"

你演示了 TextDecoder 的其他用法:

```javascript
// 假设这是从 GBK 编码的系统收到的数据
const gbkBytes = new Uint8Array([196, 227, 186, 195]);  // "你好" 的 GBK 编码

// 错误的解码方式
const wrongDecoder = new TextDecoder('utf-8');
const wrongResult = wrongDecoder.decode(gbkBytes);
console.log('UTF-8 解码 GBK 数据:', wrongResult);
// "���" 乱码

// 正确的解码方式 (如果浏览器支持 GBK)
try {
    const gbkDecoder = new TextDecoder('gbk');
    const correctResult = gbkDecoder.decode(gbkBytes);
    console.log('GBK 解码:', correctResult);
    // "你好"
} catch (e) {
    console.log('浏览器不支持 GBK 编码');
}
```

"TextDecoder 的构造函数可以接受编码名称作为参数, " 你解释, "但并不是所有浏览器都支持所有编码。UTF-8 是唯一保证支持的编码。"

你又展示了流式解码的功能:

```javascript
// 假设数据是分多次接收的
const decoder = new TextDecoder('utf-8', { stream: true });

// 第一次收到前 5 个字节
const chunk1 = new Uint8Array([228, 189, 160, 229, 165]);
const result1 = decoder.decode(chunk1, { stream: true });
console.log('第一次解码:', result1);
// "你" (只能解码完整的字符)

// 第二次收到剩余字节
const chunk2 = new Uint8Array([189, 32, 87, 111, 114, 108, 100]);
const result2 = decoder.decode(chunk2, { stream: true });
console.log('第二次解码:', result2);
// "好 World"

// 最后一次, 表示数据流结束
const result3 = decoder.decode();
console.log('最终结果:', result1 + result2 + result3);
// "你好 World"
```

"stream 选项用于处理分块接收的数据, " 你说, "这在网络传输中很常见。如果一个 UTF-8 字符跨越了两个数据块, TextDecoder 会等到下一个块到达后再解码。"

小李恍然大悟: "所以 TextEncoder 和 TextDecoder 不只是简单的转换工具, 它们还处理了很多编码的细节问题。"

"对, " 你点头, "比如 UTF-8 的多字节序列、流式处理、错误处理等。这些都是手动转换很难正确实现的。"

老张问: "那性能呢? 使用 API 会不会比手动转换慢?"

你运行了一个性能测试:

```javascript
const longText = "你好 World 😀".repeat(10000);

// 测试 TextEncoder
console.time('TextEncoder');
const encoder = new TextEncoder();
for (let i = 0; i < 100; i++) {
    encoder.encode(longText);
}
console.timeEnd('TextEncoder');
// TextEncoder: ~50ms

// 测试手动转换 (错误的方法)
console.time('Manual');
for (let i = 0; i < 100; i++) {
    const bytes = [];
    for (let j = 0; j < longText.length; j++) {
        bytes.push(longText.charCodeAt(j));
    }
    new Uint8Array(bytes);
}
console.timeEnd('Manual');
// Manual: ~200ms
```

"TextEncoder 更快, " 你指着结果, "因为它是用原生代码实现的, 而且是正确的实现。手动转换不仅慢, 还会得到错误的结果。"

---

## 最佳实践

小李修改了他的代码:

```javascript
// ❌ 错误的实现
function sendTextWrong(text) {
    const bytes = [];
    for (let i = 0; i < text.length; i++) {
        bytes.push(text.charCodeAt(i));
    }
    const buffer = new Uint8Array(bytes);
    ws.send(buffer);
}

// ✅ 正确的实现
function sendTextCorrect(text) {
    const encoder = new TextEncoder();
    const buffer = encoder.encode(text);
    ws.send(buffer);
}

// ✅ 接收端的解码
function receiveText(buffer) {
    const decoder = new TextDecoder('utf-8');
    const text = decoder.decode(buffer);
    return text;
}

// ✅ 流式解码 (用于大文件或长连接)
class StreamTextDecoder {
    constructor() {
        this.decoder = new TextDecoder('utf-8', { stream: true });
    }

    decodeChunk(chunk) {
        return this.decoder.decode(chunk, { stream: true });
    }

    finalize() {
        return this.decoder.decode();  // 完成解码
    }
}
```

"现在清楚了, " 小李说, "使用 TextEncoder 和 TextDecoder 是标准做法, 既正确又高效。"

老张补充: "而且代码也更简洁, 不需要自己处理编码的细节。"

你点头同意: "对。记住三个原则: 第一, 永远使用 TextEncoder 和 TextDecoder 进行文本和二进制数据的转换。第二, 除非有特殊需求, 否则始终使用 UTF-8 编码。第三, 对于流式数据, 使用 stream 选项来处理跨块的字符。"

小李在 PR 描述中添加了这些说明, 你们一致同意了他的修改。

会议结束后, 你回到座位, 打开笔记本。今天的代码审查让整个团队都理解了文本编码的正确处理方式, 这比单纯修复一个 bug 更有价值。

---

## 编码转换指南

**规则 1: TextEncoder 和 TextDecoder 的职责**

TextEncoder 和 TextDecoder 是浏览器提供的标准 API, 用于在字符串和二进制数据 (Uint8Array) 之间进行转换。

```javascript
// TextEncoder: 字符串 → 二进制
const encoder = new TextEncoder();
const text = "你好 World 😀";
const bytes = encoder.encode(text);
console.log(bytes);  // Uint8Array(17) [228, 189, 160, 229, 165, 189, ...]

// TextDecoder: 二进制 → 字符串
const decoder = new TextDecoder();
const decoded = decoder.decode(bytes);
console.log(decoded);  // "你好 World 😀"
```

核心职责:
- **TextEncoder**: 将 JavaScript 字符串编码为 UTF-8 字节序列
- **TextDecoder**: 将字节序列解码为 JavaScript 字符串
- **编码格式**: TextEncoder 仅支持 UTF-8, TextDecoder 支持多种编码
- **数据类型**: 输入是字符串, 输出是 Uint8Array (或相反)

---

**规则 2: UTF-8 编码的特性**

UTF-8 是一种变长编码, 不同字符占用不同数量的字节:

```javascript
const encoder = new TextEncoder();

// ASCII 字符: 1 字节
console.log(encoder.encode('A'));
// Uint8Array(1) [65]

// 欧洲字符: 2 字节
console.log(encoder.encode('é'));
// Uint8Array(2) [195, 169]

// 中文字符: 3 字节
console.log(encoder.encode('你'));
// Uint8Array(3) [228, 189, 160]

// Emoji: 4 字节
console.log(encoder.encode('😀'));
// Uint8Array(4) [240, 159, 152, 128]

// 混合文本
const text = "Hello 你好 😀";
const bytes = encoder.encode(text);
console.log(bytes.byteLength);  // 17 字节
console.log(text.length);  // 10 字符 (JavaScript 的 length 不等于字节数)
```

UTF-8 编码规则:
- **ASCII (U+0000 到 U+007F)**: 1 字节, 兼容 ASCII
- **U+0080 到 U+07FF**: 2 字节, 覆盖大部分欧洲语言
- **U+0800 到 U+FFFF**: 3 字节, 覆盖中文、日文等
- **U+10000 到 U+10FFFF**: 4 字节, 覆盖 emoji 等补充字符
- **字节长度 ≠ 字符长度**: UTF-8 是变长编码, 字节数取决于字符类型

---

**规则 3: 为什么不能手动转换**

手动使用 `charCodeAt()` 转换文本是错误的做法:

```javascript
const text = "你好 😀";

// ❌ 错误方法: 直接使用 charCodeAt
const wrongBytes = [];
for (let i = 0; i < text.length; i++) {
    wrongBytes.push(text.charCodeAt(i));
}
console.log('charCodeAt:', wrongBytes);
// [20320, 22909, 32, 55357, 56832]
// 问题 1: 中文码点 20320 超出了 Uint8Array 的 0-255 范围
// 问题 2: emoji 被拆成了两个代理对

// 转成 Uint8Array 会截断
const buffer = new Uint8Array(wrongBytes);
console.log('截断后:', Array.from(buffer));
// [96, 93, 32, 93, 0]  ❌ 数据损坏, 无法恢复

// ✅ 正确方法: 使用 TextEncoder
const encoder = new TextEncoder();
const correctBytes = encoder.encode(text);
console.log('TextEncoder:', Array.from(correctBytes));
// [228, 189, 160, 229, 165, 189, 32, 240, 159, 152, 128]
// 所有字节都在 0-255 范围内, 可以完整还原
```

手动转换的问题:
- **码点范围**: `charCodeAt()` 返回 UTF-16 码元 (0-65535), 超出 Uint8Array 的 0-255 范围
- **多字节字符**: UTF-8 将中文编码为 3 字节, 手动转换无法实现
- **代理对**: emoji 在 JavaScript 中是代理对, 手动转换会拆开
- **数据截断**: 直接放入 Uint8Array 会截断高位, 导致不可逆的数据损坏
- **性能差**: 手动循环比原生 API 慢 4 倍

---

**规则 4: TextDecoder 的编码支持**

TextDecoder 可以解码多种编码格式, 但 TextEncoder 只支持 UTF-8:

```javascript
// TextEncoder 只支持 UTF-8
const encoder = new TextEncoder();
console.log(encoder.encoding);  // "utf-8" (只读属性)

// TextDecoder 支持多种编码
const decoders = [
    new TextDecoder('utf-8'),      // UTF-8 (默认, 所有浏览器支持)
    new TextDecoder('utf-16'),     // UTF-16
    new TextDecoder('iso-8859-1'), // Latin-1
    new TextDecoder('gbk'),        // 中文 GBK (部分浏览器支持)
    new TextDecoder('shift-jis'),  // 日文 (部分浏览器支持)
];

// 检查支持的编码
try {
    const decoder = new TextDecoder('gbk');
    console.log('支持 GBK');
} catch (e) {
    console.log('不支持 GBK:', e.message);
}

// 解码不同编码的数据
const utf8Bytes = new Uint8Array([228, 189, 160, 229, 165, 189]);  // "你好" UTF-8
const gbkBytes = new Uint8Array([196, 227, 186, 195]);  // "你好" GBK

const utf8Decoder = new TextDecoder('utf-8');
console.log(utf8Decoder.decode(utf8Bytes));  // "你好"

const gbkDecoder = new TextDecoder('gbk');
console.log(gbkDecoder.decode(gbkBytes));  // "你好" (如果浏览器支持)
```

编码支持规则:
- **TextEncoder**: 只支持 UTF-8, 无构造参数
- **TextDecoder**: 支持多种编码, 通过构造参数指定
- **浏览器兼容性**: UTF-8 保证支持, 其他编码视浏览器而定
- **错误处理**: 不支持的编码会抛出 RangeError
- **默认编码**: 不指定参数时, TextDecoder 默认使用 UTF-8

---

**规则 5: 流式解码 (Stream Mode)**

对于分块接收的数据, 使用流式解码处理跨块字符:

```javascript
const decoder = new TextDecoder('utf-8', { stream: true });

// 模拟分块接收数据
// "你好" 的 UTF-8 编码是 [228, 189, 160, 229, 165, 189]
// 假设数据被拆成两块, 第一块在字符中间被截断

// 第一块: 前 4 个字节
const chunk1 = new Uint8Array([228, 189, 160, 229]);
const text1 = decoder.decode(chunk1, { stream: true });
console.log('第一块:', text1);
// "你" (只解码了完整的第一个字符, 第二个字符不完整, 保留在缓冲区)

// 第二块: 剩余 2 个字节
const chunk2 = new Uint8Array([165, 189]);
const text2 = decoder.decode(chunk2, { stream: true });
console.log('第二块:', text2);
// "好" (与缓冲区的字节组合, 完成第二个字符的解码)

// 最后调用 (无参数), 表示流结束
const text3 = decoder.decode();
console.log('最终文本:', text1 + text2 + text3);
// "你好"

// ❌ 如果不使用 stream 模式
const noStreamDecoder = new TextDecoder('utf-8');
const wrongText1 = noStreamDecoder.decode(chunk1);
console.log('非流式第一块:', wrongText1);
// "你�" (不完整的字节被解码为替代字符 U+FFFD)
```

流式解码的使用场景:

```javascript
// 场景 1: WebSocket 接收大文件
const decoder = new TextDecoder('utf-8', { stream: true });
let fullText = '';

ws.onmessage = (event) => {
    const chunk = new Uint8Array(event.data);
    fullText += decoder.decode(chunk, { stream: true });
};

ws.onclose = () => {
    fullText += decoder.decode();  // 完成解码
    console.log('完整文本:', fullText);
};

// 场景 2: Fetch 流式响应
async function fetchLargeText(url) {
    const response = await fetch(url);
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8', { stream: true });
    let text = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        text += decoder.decode(value, { stream: true });
    }

    text += decoder.decode();  // 完成
    return text;
}

// 场景 3: 自定义流处理类
class StreamTextDecoder {
    constructor(encoding = 'utf-8') {
        this.decoder = new TextDecoder(encoding, { stream: true });
        this.text = '';
    }

    addChunk(chunk) {
        this.text += this.decoder.decode(chunk, { stream: true });
    }

    finish() {
        this.text += this.decoder.decode();  // 完成解码
        return this.text;
    }
}
```

流式解码规则:
- **stream: true**: 构造函数选项, 启用流式模式
- **{ stream: true }**: decode() 参数, 表示后续还有数据
- **decode()**: 无参数调用, 表示流结束, 输出缓冲区剩余字节
- **跨块字符**: 不完整的字节序列会保留在内部缓冲区, 等待下一块
- **重用解码器**: 同一个 TextDecoder 实例可以连续解码多个块
- **性能优化**: 避免每次都创建新的解码器实例

---

**规则 6: 错误处理与容错**

TextDecoder 的错误处理选项:

```javascript
// 默认模式: 替换无效字节为 U+FFFD (�)
const decoder1 = new TextDecoder('utf-8');
const invalidBytes = new Uint8Array([255, 254, 253]);  // 无效的 UTF-8 序列
console.log(decoder1.decode(invalidBytes));
// "���" (3 个替代字符)

// 严格模式: 遇到无效字节抛出错误
const decoder2 = new TextDecoder('utf-8', { fatal: true });
try {
    decoder2.decode(invalidBytes);
} catch (e) {
    console.error('解码错误:', e.message);
    // TypeError: The encoded data was not valid
}

// 忽略 BOM (Byte Order Mark)
const bytesWithBOM = new Uint8Array([0xEF, 0xBB, 0xBF, 65, 66, 67]);  // BOM + "ABC"
const decoder3 = new TextDecoder('utf-8', { ignoreBOM: false });
console.log(decoder3.decode(bytesWithBOM));
// "\uFEFFABC" (包含 BOM 字符)

const decoder4 = new TextDecoder('utf-8', { ignoreBOM: true });
console.log(decoder4.decode(bytesWithBOM));
// "ABC" (自动移除 BOM)
```

错误处理规则:
- **fatal: false** (默认): 无效字节替换为 U+FFFD (�), 继续解码
- **fatal: true**: 遇到无效字节抛出 TypeError, 停止解码
- **ignoreBOM: false** (默认): 保留 BOM 字符
- **ignoreBOM: true**: 自动移除开头的 BOM 字符
- **生产环境**: 通常使用默认模式, 容错性更好
- **严格验证**: 需要保证数据完整性时使用 fatal: true

---

**规则 7: 实际应用场景**

TextEncoder 和 TextDecoder 的常见使用场景:

**场景 1: WebSocket 二进制传输**
```javascript
// 发送端
function sendMessage(ws, text) {
    const encoder = new TextEncoder();
    const bytes = encoder.encode(text);
    ws.send(bytes.buffer);  // 发送 ArrayBuffer
}

// 接收端
ws.onmessage = (event) => {
    const decoder = new TextDecoder('utf-8');
    const bytes = new Uint8Array(event.data);
    const text = decoder.decode(bytes);
    console.log('收到消息:', text);
};
```

**场景 2: 文件读取与保存**
```javascript
// 读取文本文件
async function readTextFile(file) {
    const buffer = await file.arrayBuffer();
    const decoder = new TextDecoder('utf-8');
    return decoder.decode(buffer);
}

// 保存文本到文件
function saveTextFile(text, filename) {
    const encoder = new TextEncoder();
    const bytes = encoder.encode(text);
    const blob = new Blob([bytes], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
}
```

**场景 3: Fetch 流式处理**
```javascript
async function fetchTextStream(url) {
    const response = await fetch(url);
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8', { stream: true });
    let text = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        text += decoder.decode(value, { stream: true });
        console.log('已接收:', text.length, '字符');
    }

    text += decoder.decode();
    return text;
}
```

**场景 4: 自定义二进制协议**
```javascript
// 编码: 消息头 (4 字节长度) + 消息体 (UTF-8 文本)
function encodeMessage(text) {
    const encoder = new TextEncoder();
    const body = encoder.encode(text);
    const header = new Uint32Array([body.byteLength]);
    const message = new Uint8Array(4 + body.byteLength);
    message.set(new Uint8Array(header.buffer), 0);
    message.set(body, 4);
    return message;
}

// 解码: 读取长度头, 解码消息体
function decodeMessage(bytes) {
    const header = new Uint32Array(bytes.buffer, 0, 1);
    const length = header[0];
    const body = new Uint8Array(bytes.buffer, 4, length);
    const decoder = new TextDecoder('utf-8');
    return decoder.decode(body);
}
```

**场景 5: 计算文本字节大小**
```javascript
// 计算字符串的 UTF-8 字节长度
function getByteLength(text) {
    const encoder = new TextEncoder();
    return encoder.encode(text).byteLength;
}

console.log(getByteLength('Hello'));    // 5 字节
console.log(getByteLength('你好'));     // 6 字节
console.log(getByteLength('😀'));       // 4 字节
```

---

**规则 8: 性能优化与最佳实践**

TextEncoder 和 TextDecoder 的性能考虑:

```javascript
// ✅ 最佳实践 1: 重用编码器实例
const encoder = new TextEncoder();  // 创建一次
const decoder = new TextDecoder();

for (let i = 0; i < 1000; i++) {
    const bytes = encoder.encode(text);  // 重用实例
    const decoded = decoder.decode(bytes);
}

// ❌ 避免: 每次都创建新实例
for (let i = 0; i < 1000; i++) {
    const bytes = new TextEncoder().encode(text);  // 低效
}

// ✅ 最佳实践 2: 批量编码
const texts = ['text1', 'text2', 'text3'];
const encoder = new TextEncoder();
const encoded = texts.map(t => encoder.encode(t));  // 一次性编码

// ✅ 最佳实践 3: 流式处理大文件
async function processLargeFile(file) {
    const decoder = new TextDecoder('utf-8', { stream: true });
    const reader = file.stream().getReader();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        processChunk(chunk);  // 逐块处理, 避免内存溢出
    }

    const final = decoder.decode();
    processFinal(final);
}

// ✅ 最佳实践 4: 预计算字节长度
function encodeWithLength(text) {
    const encoder = new TextEncoder();
    const bytes = encoder.encode(text);
    // 在协议头中记录字节长度, 方便接收端解析
    return { length: bytes.byteLength, data: bytes };
}
```

性能优化原则:
- **重用实例**: 编码器实例可以重用, 避免重复创建
- **批量操作**: 尽量批量编码/解码, 减少函数调用开销
- **流式处理**: 大文件使用流式模式, 避免内存溢出
- **避免拼接**: 字符串拼接性能差, 使用数组 join 或 TextDecoder
- **预计算长度**: 需要长度信息时, 使用 byteLength 而非编码后再计算
- **原生性能**: TextEncoder/Decoder 比手动实现快 4-10 倍

---

**事故档案编号**: NETWORK-2024-1942
**影响范围**: TextEncoder, TextDecoder, UTF-8, 字符编码, 二进制数据
**根本原因**: 手动使用 charCodeAt() 转换文本导致数据损坏, 不理解 UTF-8 变长编码
**学习成本**: 低 (API 简单, 但需理解编码原理)

这是 JavaScript 世界第 142 次被记录的网络与数据事故。TextEncoder 和 TextDecoder 是浏览器提供的标准 API, 用于在 JavaScript 字符串和二进制数据之间进行转换。TextEncoder 将字符串编码为 UTF-8 字节序列, TextDecoder 将字节序列解码为字符串。UTF-8 是变长编码, ASCII 字符占 1 字节, 中文占 3 字节, emoji 占 4 字节。手动使用 charCodeAt() 转换文本会导致数据截断和损坏, 因为 UTF-16 码元超出 Uint8Array 的 0-255 范围。流式解码 (stream: true) 用于处理分块接收的数据, 自动处理跨块字符。理解文本编码的底层机制是正确处理二进制数据传输的基础。

---
