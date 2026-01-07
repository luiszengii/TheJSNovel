《第 136 次记录：文本选区的秘密 —— Selection 与 Range 操作》

## 复制功能失效事件

周三下午 2 点 47 分，你收到产品经理的紧急消息："用户说复制代码功能不工作了，点击复制按钮后粘贴出来的内容是错的！"

你立刻打开线上的技术文档站点，找到一个代码示例，点击右上角的"复制代码"按钮，然后粘贴到记事本 —— 粘贴出来的内容确实不对。代码块的内容是：

```javascript
function hello() {
  console.log('Hello World');
}
```

但粘贴出来的却是：

```
functionhello() {console.log('Hello World');}
```

所有的换行和缩进都消失了，而且 `function` 和 `hello` 之间的空格也没了。你检查了代码，发现复制功能是这样实现的：

```javascript
copyButton.addEventListener('click', () => {
  const codeBlock = document.querySelector('pre code');
  const text = codeBlock.textContent;

  navigator.clipboard.writeText(text).then(() => {
    showToast('复制成功');
  });
});
```

"看起来没问题啊，" 你困惑地想，"`textContent` 应该能获取到完整的文本内容才对..."

你在控制台测试：

```javascript
const codeBlock = document.querySelector('pre code');
console.log(codeBlock.textContent);
// 输出: "function hello() {\n  console.log('Hello World');\n}"
// 换行符和空格都在
```

"`textContent` 的内容是正确的，" 你自言自语，"那问题出在哪里？"

前端架构师老周走过来，看了一眼代码："你获取的是 `code` 元素的文本，但用户可能只选中了其中一部分。你应该用 Selection API 获取用户实际选中的内容。"

## Selection API 基础

老周展示了 Selection API 的基本用法：

```javascript
// 获取当前选区
const selection = window.getSelection();

// 选区的基本信息
console.log('选中的文本:', selection.toString());
console.log('选区数量:', selection.rangeCount);
console.log('锚点节点:', selection.anchorNode);
console.log('锚点偏移:', selection.anchorOffset);
console.log('焦点节点:', selection.focusNode);
console.log('焦点偏移:', selection.focusOffset);
console.log('是否折叠:', selection.isCollapsed); // true 表示光标，false 表示选区

// 测试：在页面上选中一段文本
// 然后在控制台运行上面的代码，查看输出
```

老周解释道："Selection 代表用户当前选中的文本范围。它包含一个或多个 Range 对象，Range 代表文档中的一个连续区域。"

你立刻写了一个测试：

```javascript
// 监听选区变化
document.addEventListener('selectionchange', () => {
  const selection = window.getSelection();

  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    console.log('选中的文本:', selection.toString());
    console.log('Range 信息:', {
      startContainer: range.startContainer,
      startOffset: range.startOffset,
      endContainer: range.endContainer,
      endOffset: range.endOffset,
      collapsed: range.collapsed
    });
  }
});
```

你在页面上选中一段文本，控制台立刻输出了详细信息：

```
选中的文本: Hello World
Range 信息: {
  startContainer: #text "Hello World"
  startOffset: 0
  endContainer: #text "Hello World"
  endOffset: 11
  collapsed: false
}
```

"原来如此，" 你恍然大悟，"Selection 是用户选中的内容，Range 是具体的文档范围。"

## Range 对象详解

老周展示了 Range 的核心概念：

```javascript
// 创建一个 Range 对象
const range = document.createRange();

// Range 的四个关键属性：
// - startContainer: 起始节点
// - startOffset: 起始偏移量
// - endContainer: 结束节点
// - endOffset: 结束偏移量

// 示例 1: 选择一个元素的全部内容
const paragraph = document.querySelector('p');
range.selectNodeContents(paragraph);

console.log('Range 内容:', range.toString());
console.log('Range HTML:', range.cloneContents());

// 示例 2: 选择特定范围
const textNode = paragraph.firstChild;
range.setStart(textNode, 0);      // 从文本节点的第 0 个字符开始
range.setEnd(textNode, 5);        // 到第 5 个字符结束

console.log('选中的文本:', range.toString()); // 前 5 个字符

// 示例 3: 选择整个元素节点（包括标签）
range.selectNode(paragraph); // 包含 <p> 标签本身

// 示例 4: Range 的位置关系
const anotherRange = document.createRange();
anotherRange.selectNodeContents(document.body);

const comparison = range.compareBoundaryPoints(
  Range.START_TO_START,
  anotherRange
);

console.log('位置关系:', comparison);
// -1: range 在 anotherRange 之前
//  0: 相同位置
//  1: range 在 anotherRange 之后
```

老周特别强调："Range 的 startContainer 和 endContainer 可以是任何节点类型（元素节点或文本节点），offset 的含义取决于节点类型：如果是文本节点，offset 是字符位置；如果是元素节点，offset 是子节点索引。"

```javascript
// 文本节点的 offset：字符位置
const textNode = document.createTextNode('Hello World');
const range = document.createRange();
range.setStart(textNode, 0);   // 从 'H' 开始
range.setEnd(textNode, 5);     // 到 'o' 结束（不包括）
console.log(range.toString()); // "Hello"

// 元素节点的 offset：子节点索引
const div = document.createElement('div');
div.innerHTML = '<span>A</span><span>B</span><span>C</span>';

const elementRange = document.createRange();
elementRange.setStart(div, 0);   // 从第 0 个子节点开始（<span>A</span>）
elementRange.setEnd(div, 2);     // 到第 2 个子节点结束（不包括 <span>C</span>）

console.log(elementRange.cloneContents());
// <span>A</span><span>B</span>
```

## 编程式操作选区

老周展示了如何用代码操作选区：

```javascript
// 1. 选中特定元素的内容
function selectElementContent(element) {
  const range = document.createRange();
  range.selectNodeContents(element);

  const selection = window.getSelection();
  selection.removeAllRanges(); // 清除现有选区
  selection.addRange(range);    // 添加新选区
}

// 测试
const codeBlock = document.querySelector('pre code');
selectElementContent(codeBlock);

// 2. 选中文本的特定部分
function selectTextRange(element, startOffset, endOffset) {
  const range = document.createRange();
  const textNode = element.firstChild;

  if (textNode && textNode.nodeType === 3) { // 文本节点
    range.setStart(textNode, startOffset);
    range.setEnd(textNode, endOffset);

    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }
}

// 测试：选中前 10 个字符
const paragraph = document.querySelector('p');
selectTextRange(paragraph, 0, 10);

// 3. 清除选区
function clearSelection() {
  const selection = window.getSelection();
  selection.removeAllRanges();
}

// 4. 获取选区的边界矩形
function getSelectionRect() {
  const selection = window.getSelection();

  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    console.log('选区位置:', {
      x: rect.x,
      y: rect.y,
      width: rect.width,
      height: rect.height
    });

    return rect;
  }

  return null;
}

// 5. 在选区插入内容
function insertAtSelection(html) {
  const selection = window.getSelection();

  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    range.deleteContents(); // 删除选中内容

    const fragment = range.createContextualFragment(html);
    range.insertNode(fragment);
  }
}

// 测试：选中一段文本，然后运行
insertAtSelection('<strong>替换内容</strong>');
```

## 修复复制功能

老周帮你重构了复制功能：

```javascript
class CodeBlockCopy {
  constructor(codeBlock, button) {
    this.codeBlock = codeBlock;
    this.button = button;
    this.init();
  }

  init() {
    this.button.addEventListener('click', () => {
      this.copyCode();
    });
  }

  async copyCode() {
    // 方法 1: 使用 Selection API 选中内容后复制
    this.selectCodeBlock();

    try {
      // 执行浏览器的复制命令
      const success = document.execCommand('copy');

      if (success) {
        this.showToast('复制成功');
      } else {
        // 降级到 Clipboard API
        await this.fallbackCopy();
      }
    } catch (error) {
      await this.fallbackCopy();
    } finally {
      // 清除选区
      window.getSelection().removeAllRanges();
    }
  }

  selectCodeBlock() {
    const range = document.createRange();
    range.selectNodeContents(this.codeBlock);

    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }

  async fallbackCopy() {
    // 降级方案：使用 Clipboard API
    const text = this.codeBlock.textContent;
    await navigator.clipboard.writeText(text);
    this.showToast('复制成功');
  }

  showToast(message) {
    // 显示提示
    console.log(message);
  }
}

// 使用复制功能
const codeBlock = document.querySelector('pre code');
const copyButton = document.querySelector('.copy-button');
new CodeBlockCopy(codeBlock, copyButton);
```

测试后，你发现复制功能正常了。但老周说："还有个问题。如果用户已经选中了代码块的一部分，点击复制按钮应该只复制选中的内容，而不是整个代码块。"

你立刻改进了代码：

```javascript
class SmartCodeCopy {
  constructor(codeBlock, button) {
    this.codeBlock = codeBlock;
    this.button = button;
    this.init();
  }

  init() {
    this.button.addEventListener('click', () => {
      this.copyCode();
    });
  }

  async copyCode() {
    const selection = window.getSelection();
    let textToCopy = '';

    // 检查用户是否已选中代码块内的内容
    if (this.hasSelectionInCodeBlock(selection)) {
      // 用户已选中内容，复制选中的部分
      textToCopy = selection.toString();
      console.log('复制用户选中的内容');
    } else {
      // 用户未选中，复制整个代码块
      textToCopy = this.codeBlock.textContent;
      console.log('复制整个代码块');
    }

    try {
      await navigator.clipboard.writeText(textToCopy);
      this.showToast(`已复制 ${textToCopy.length} 个字符`);
    } catch (error) {
      console.error('复制失败:', error);
      this.showToast('复制失败，请手动复制');
    }
  }

  hasSelectionInCodeBlock(selection) {
    if (selection.rangeCount === 0) return false;
    if (selection.isCollapsed) return false; // 只是光标，没有选区

    const range = selection.getRangeAt(0);

    // 检查选区是否在代码块内
    return this.codeBlock.contains(range.commonAncestorContainer);
  }

  showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 2000);
  }
}
```

## Range 的实用方法

老周展示了 Range 的其他实用方法：

```javascript
// 1. 提取选区内容（移除原内容）
const range = document.createRange();
range.selectNodeContents(document.querySelector('p'));

const fragment = range.extractContents();
console.log('提取的内容:', fragment);
// 原位置的内容已被删除

// 2. 克隆选区内容（保留原内容）
const clonedFragment = range.cloneContents();
console.log('克隆的内容:', clonedFragment);
// 原位置的内容仍然存在

// 3. 删除选区内容
range.deleteContents();
// 选区内容被删除

// 4. 插入节点
const span = document.createElement('span');
span.textContent = '插入的内容';
range.insertNode(span);

// 5. 包围选区内容
const wrapper = document.createElement('mark');
range.surroundContents(wrapper);
// 选区内容被 <mark> 标签包围

// 6. 折叠选区
range.collapse(true);  // 折叠到起点
range.collapse(false); // 折叠到终点

// 7. 获取选区的 HTML
function getRangeHTML(range) {
  const fragment = range.cloneContents();
  const div = document.createElement('div');
  div.appendChild(fragment);
  return div.innerHTML;
}

// 8. 检查节点是否在选区内
function isNodeInRange(node, range) {
  return range.isPointInRange(node, 0);
}
```

## 实战：富文本编辑器基础

老周展示了如何用 Selection 和 Range 实现基本的富文本编辑功能：

```javascript
class SimpleEditor {
  constructor(element) {
    this.element = element;
    this.element.contentEditable = true;
    this.init();
  }

  init() {
    // 绑定工具栏按钮
    document.querySelector('.bold-btn').addEventListener('click', () => {
      this.formatSelection('bold');
    });

    document.querySelector('.italic-btn').addEventListener('click', () => {
      this.formatSelection('italic');
    });

    document.querySelector('.highlight-btn').addEventListener('click', () => {
      this.highlightSelection();
    });

    document.querySelector('.insert-link-btn').addEventListener('click', () => {
      this.insertLink();
    });
  }

  formatSelection(command) {
    // 使用 document.execCommand 格式化选区
    document.execCommand(command, false, null);
  }

  highlightSelection() {
    const selection = window.getSelection();

    if (selection.rangeCount === 0) return;

    const range = selection.getRangeAt(0);

    // 包围选区内容
    const mark = document.createElement('mark');
    mark.style.backgroundColor = 'yellow';

    try {
      range.surroundContents(mark);
    } catch (error) {
      // surroundContents 失败时的降级方案
      const fragment = range.extractContents();
      mark.appendChild(fragment);
      range.insertNode(mark);
    }
  }

  insertLink() {
    const url = prompt('请输入链接地址:');
    if (!url) return;

    const selection = window.getSelection();

    if (selection.rangeCount === 0) return;

    const range = selection.getRangeAt(0);
    const selectedText = range.toString();

    // 创建链接
    const link = document.createElement('a');
    link.href = url;
    link.textContent = selectedText || url;

    // 插入链接
    range.deleteContents();
    range.insertNode(link);

    // 将光标移到链接后面
    range.setStartAfter(link);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
  }

  getSelectedText() {
    const selection = window.getSelection();
    return selection.toString();
  }

  getSelectedHTML() {
    const selection = window.getSelection();

    if (selection.rangeCount === 0) return '';

    const range = selection.getRangeAt(0);
    const fragment = range.cloneContents();

    const div = document.createElement('div');
    div.appendChild(fragment);

    return div.innerHTML;
  }
}

// 使用编辑器
const editor = new SimpleEditor(document.querySelector('.editor'));
```

## 跨元素选区处理

老周展示了如何处理跨多个元素的选区：

```javascript
// 获取选区中的所有元素
function getElementsInSelection() {
  const selection = window.getSelection();

  if (selection.rangeCount === 0) return [];

  const range = selection.getRangeAt(0);
  const container = range.commonAncestorContainer;

  // 如果公共祖先是文本节点，获取其父元素
  const parent = container.nodeType === 3
    ? container.parentElement
    : container;

  const elements = [];
  const walker = document.createTreeWalker(
    parent,
    NodeFilter.SHOW_ELEMENT,
    {
      acceptNode: (node) => {
        return range.intersectsNode(node)
          ? NodeFilter.FILTER_ACCEPT
          : NodeFilter.FILTER_REJECT;
      }
    }
  );

  let node;
  while (node = walker.nextNode()) {
    elements.push(node);
  }

  return elements;
}

// 测试：选中跨多个段落的文本
// 然后运行这个函数，查看选区包含的所有元素
const elements = getElementsInSelection();
console.log('选区包含的元素:', elements);

// 批量处理选区中的元素
function processSelectionElements(callback) {
  const elements = getElementsInSelection();
  elements.forEach(callback);
}

// 示例：高亮选区中的所有段落
processSelectionElements((element) => {
  if (element.tagName === 'P') {
    element.style.backgroundColor = 'yellow';
  }
});
```

下午 5 点，你完成了复制功能的重构。新的实现不仅修复了换行丢失的问题，还能智能识别用户选中的内容。你给产品经理发了消息："复制功能已修复，现在可以正确保留代码格式，并且支持部分复制。" 测试人员确认问题解决后，你将代码部署到了生产环境。

---

## 技术档案：Selection 与 Range 核心机制

**规则 1: Selection 代表用户选区，Range 代表文档范围**

Selection 对象代表用户当前选中的文本范围，包含一个或多个 Range 对象。Range 对象代表文档中的一个连续区域，由起始点和结束点定义。

```javascript
// 获取当前选区
const selection = window.getSelection();

// Selection 的关键属性：
console.log('选中的文本:', selection.toString());
console.log('Range 数量:', selection.rangeCount); // 通常是 0 或 1
console.log('是否折叠:', selection.isCollapsed); // true: 光标, false: 选区

// 锚点（anchor）：用户开始选择的位置
console.log('锚点节点:', selection.anchorNode);
console.log('锚点偏移:', selection.anchorOffset);

// 焦点（focus）：用户结束选择的位置（当前光标位置）
console.log('焦点节点:', selection.focusNode);
console.log('焦点偏移:', selection.focusOffset);

// 获取 Range 对象
if (selection.rangeCount > 0) {
  const range = selection.getRangeAt(0);

  // Range 的四个关键属性：
  console.log('起始容器:', range.startContainer);
  console.log('起始偏移:', range.startOffset);
  console.log('结束容器:', range.endContainer);
  console.log('结束偏移:', range.endOffset);
  console.log('是否折叠:', range.collapsed);
}

// Selection 与 Range 的关系：
// - Selection 是用户可见的选区（蓝色高亮）
// - Range 是底层的文档范围对象
// - 一个 Selection 可以包含多个 Range（某些浏览器支持）
// - 通常情况下 Selection 只包含一个 Range
```

**规则 2: Range 的 offset 含义取决于容器类型**

Range 的 startOffset 和 endOffset 的含义取决于容器节点的类型：文本节点是字符位置，元素节点是子节点索引。

```javascript
// 场景 1: 文本节点的 offset（字符位置）
const textNode = document.createTextNode('Hello World');
const range1 = document.createRange();

range1.setStart(textNode, 0);   // 从第 0 个字符 'H' 开始
range1.setEnd(textNode, 5);     // 到第 5 个字符（不包括），即 'o' 后面

console.log(range1.toString()); // "Hello"

// 场景 2: 元素节点的 offset（子节点索引）
const div = document.createElement('div');
div.innerHTML = '<span>A</span><span>B</span><span>C</span>';

const range2 = document.createRange();
range2.setStart(div, 0);   // 从第 0 个子节点 <span>A</span> 开始
range2.setEnd(div, 2);     // 到第 2 个子节点（不包括），即 <span>B</span> 后面

// 克隆 Range 内容
const fragment = range2.cloneContents();
console.log(fragment); // <span>A</span><span>B</span>

// 实际应用：选中元素的部分子节点
const parent = document.querySelector('.container');
const range = document.createRange();

// 选中第 2 到第 5 个子元素
range.setStart(parent, 1);  // 从索引 1 开始（第 2 个）
range.setEnd(parent, 5);    // 到索引 5 结束（不包括第 6 个）

const selection = window.getSelection();
selection.removeAllRanges();
selection.addRange(range);
```

**规则 3: 编程式操作选区的标准流程**

通过 Range API 创建范围，然后添加到 Selection 中，实现编程式选区控制。操作完成后应清除选区。

```javascript
// 标准流程：创建 Range → 设置范围 → 添加到 Selection

// 1. 选中元素的全部内容
function selectElement(element) {
  const range = document.createRange();
  range.selectNodeContents(element); // 选中元素内部所有内容

  const selection = window.getSelection();
  selection.removeAllRanges(); // 清除现有选区
  selection.addRange(range);    // 添加新选区
}

// 2. 选中特定文本范围
function selectTextRange(element, start, end) {
  const range = document.createRange();
  const textNode = element.firstChild;

  if (textNode && textNode.nodeType === 3) {
    range.setStart(textNode, start);
    range.setEnd(textNode, end);

    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }
}

// 3. 清除选区
function clearSelection() {
  window.getSelection().removeAllRanges();
}

// 4. 获取选区位置（用于显示工具栏）
function getSelectionRect() {
  const selection = window.getSelection();

  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    return range.getBoundingClientRect();
  }

  return null;
}

// 使用示例：点击按钮选中代码块
document.querySelector('.select-code-btn').addEventListener('click', () => {
  const codeBlock = document.querySelector('pre code');
  selectElement(codeBlock);
});

// 选中后显示复制按钮
document.addEventListener('selectionchange', () => {
  const rect = getSelectionRect();
  if (rect) {
    showCopyButton(rect.x, rect.y);
  } else {
    hideCopyButton();
  }
});
```

**规则 4: Range 的内容操作方法各有用途**

Range 提供多种方法操作选区内容：提取（移除）、克隆（保留）、删除、插入、包围。选择合适的方法避免副作用。

```javascript
const range = document.createRange();
range.selectNodeContents(document.querySelector('p'));

// 1. extractContents() - 提取内容（从文档移除）
const extracted = range.extractContents();
console.log('提取的内容:', extracted);
// ⚠️ 原位置的内容已被删除

// 2. cloneContents() - 克隆内容（保留原内容）
const cloned = range.cloneContents();
console.log('克隆的内容:', cloned);
// ✅ 原位置的内容仍然存在

// 3. deleteContents() - 删除内容
range.deleteContents();
// 选区内容被删除

// 4. insertNode() - 插入节点
const span = document.createElement('span');
span.textContent = '插入的内容';
range.insertNode(span);
// 在 Range 起点插入节点

// 5. surroundContents() - 包围内容
const mark = document.createElement('mark');
range.surroundContents(mark);
// 选区内容被 <mark> 标签包围

// ⚠️ surroundContents 的限制：
// - 只能包围完整的节点
// - 如果 Range 横跨多个元素，可能失败

// 降级方案：
function surroundWithElement(range, element) {
  try {
    range.surroundContents(element);
  } catch (error) {
    // 如果 surroundContents 失败，使用 extractContents + insertNode
    const contents = range.extractContents();
    element.appendChild(contents);
    range.insertNode(element);
  }
}

// 6. 获取 Range 的 HTML 内容
function getRangeHTML(range) {
  const fragment = range.cloneContents();
  const div = document.createElement('div');
  div.appendChild(fragment);
  return div.innerHTML;
}
```

**规则 5: 监听 selectionchange 事件追踪选区变化**

使用 `selectionchange` 事件监听用户选区变化，实现智能工具栏、实时预览等功能。注意事件可能频繁触发，需要防抖优化。

```javascript
// 监听选区变化
document.addEventListener('selectionchange', () => {
  const selection = window.getSelection();

  console.log('选区变化');
  console.log('选中的文本:', selection.toString());
  console.log('是否有选区:', !selection.isCollapsed);
});

// 实战：显示选区工具栏
let toolbarTimeout;

document.addEventListener('selectionchange', () => {
  const selection = window.getSelection();

  // 防抖：等待用户停止选择
  clearTimeout(toolbarTimeout);
  toolbarTimeout = setTimeout(() => {
    if (selection.isCollapsed || selection.toString().trim() === '') {
      // 没有选区或选区为空，隐藏工具栏
      hideToolbar();
    } else {
      // 有选区，显示工具栏
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      showToolbar(rect.x, rect.y - 40); // 工具栏显示在选区上方
    }
  }, 100);
});

function showToolbar(x, y) {
  const toolbar = document.querySelector('.selection-toolbar');
  toolbar.style.display = 'block';
  toolbar.style.left = x + 'px';
  toolbar.style.top = y + 'px';
}

function hideToolbar() {
  const toolbar = document.querySelector('.selection-toolbar');
  toolbar.style.display = 'none';
}

// 工具栏按钮事件
document.querySelector('.bold-btn').addEventListener('click', () => {
  document.execCommand('bold', false, null);
});

document.querySelector('.highlight-btn').addEventListener('click', () => {
  const selection = window.getSelection();
  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    const mark = document.createElement('mark');
    mark.style.backgroundColor = 'yellow';

    try {
      range.surroundContents(mark);
    } catch (error) {
      // 降级方案
      const contents = range.extractContents();
      mark.appendChild(contents);
      range.insertNode(mark);
    }
  }
});
```

**规则 6: 实现智能复制功能的最佳实践**

复制功能应优先检测用户选区，然后降级到复制整个元素。使用 Clipboard API 或 execCommand，并提供友好的用户反馈。

```javascript
class SmartCopyButton {
  constructor(element, button) {
    this.element = element;
    this.button = button;
    this.init();
  }

  init() {
    this.button.addEventListener('click', async () => {
      await this.copy();
    });
  }

  async copy() {
    const selection = window.getSelection();
    let textToCopy = '';
    let copyMethod = '';

    // 1. 检查用户是否选中了元素内的内容
    if (this.hasSelectionInElement(selection)) {
      textToCopy = selection.toString();
      copyMethod = '用户选区';
    } else {
      // 2. 用户未选中，复制整个元素
      textToCopy = this.element.textContent;
      copyMethod = '整个元素';
    }

    try {
      // 方法 1: 使用 Clipboard API（现代浏览器）
      await navigator.clipboard.writeText(textToCopy);
      this.showFeedback(`已复制 ${textToCopy.length} 个字符（${copyMethod}）`);
    } catch (error) {
      // 方法 2: 降级到 execCommand
      this.fallbackCopy(textToCopy);
    }
  }

  hasSelectionInElement(selection) {
    if (selection.rangeCount === 0) return false;
    if (selection.isCollapsed) return false;

    const range = selection.getRangeAt(0);
    return this.element.contains(range.commonAncestorContainer);
  }

  fallbackCopy(text) {
    // 创建临时 textarea
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);

    // 选中并复制
    textarea.select();
    const success = document.execCommand('copy');

    document.body.removeChild(textarea);

    if (success) {
      this.showFeedback('已复制');
    } else {
      this.showFeedback('复制失败，请手动复制');
    }
  }

  showFeedback(message) {
    const toast = document.createElement('div');
    toast.className = 'copy-toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('show');
    }, 10);

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 2000);
  }
}

// 使用智能复制按钮
document.querySelectorAll('pre code').forEach((codeBlock) => {
  const button = codeBlock.parentElement.querySelector('.copy-btn');
  if (button) {
    new SmartCopyButton(codeBlock, button);
  }
});
```

---

**记录者注**:

Selection API 和 Range API 是浏览器提供的文本选区操作接口。Selection 代表用户当前选中的文本范围，Range 代表文档中的一个连续区域。两者配合使用可以实现复制功能、富文本编辑、选区高亮、智能工具栏等功能。

关键在于理解 Selection 和 Range 的关系、Range 的四个边界属性（startContainer、startOffset、endContainer、endOffset）、offset 在不同节点类型中的含义（文本节点是字符位置，元素节点是子节点索引）。实际应用中需要处理用户选区和编程式选区两种场景，监听 selectionchange 事件实现动态交互，使用 Range 的各种方法（extract、clone、delete、insert、surround）操作选区内容。

记住：**Selection 代表用户选区，Range 代表文档范围；offset 的含义取决于容器类型；编程式操作选区需要创建 Range 并添加到 Selection；Range 提供多种内容操作方法；监听 selectionchange 追踪选区变化；智能复制功能应优先检测用户选区**。掌握 Selection 和 Range API 是实现高级文本交互功能的基础。
