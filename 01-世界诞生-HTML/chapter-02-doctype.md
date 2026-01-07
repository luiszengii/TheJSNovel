《第2次记录：模式裂痕事故 —— Doctype 与渲染模式》

---

## 事故现场

周二上午九点,你刚到办公室坐下,就收到一封标记为"高优先级"的邮件。主题是:"紧急:客户说我们的网站在他那边完全乱套了。"

办公室里很安静,同事们都还没来齐。你喝了一口咖啡,打开附件里的截图,手指停在了鼠标上——你倒吸一口凉气。那个你精心设计的后台管理界面，在客户的浏览器里完全走样了：本该整齐排列的按钮挤成一团，宽度设置的 `100px` 的侧边栏占据了半个屏幕，`margin: 10px` 的间距看起来有五十像素那么大。

"应该是浏览器兼容性问题，"你安慰自己，"可能是IE的老版本。"但客户的回复让你愣住：Chrome 最新版，Windows 11。

你在自己的Chrome上打开同样的页面——完美无缺。你让客户发来页面源代码，逐行对比，一模一样。你甚至远程到客户的电脑上，打开DevTools...

当你看到控制台顶部的提示时，手指停在了空中：

```
Quirks Mode enabled
```

怪异模式？但你的页面明明有Doctype声明...等等，有吗？

你切换到Sources面板，查看HTML源码。第一行，空白。第二行，空白。第三行...一个被你遗忘的注释：

```html
<!-- 这是备份版本，暂时保留 -->

<!DOCTYPE html>
<html>
...
```

你的心沉了下去。那个注释，在Doctype之前。

---

## 深入迷雾

上午九点半,产品经理发来消息:"找到原因了吗?客户很着急,说影响了他们的业务演示。"

"正在排查,"你快速回复,心里开始发慌。你立刻在本地创建了一个测试文件,重现这个问题:

```html
<!-- 注释 -->
<!DOCTYPE html>
<html>
<head>
    <style>
        .box {
            width: 100px;
            height: 100px;
            background: blue;
        }
    </style>
</head>
<body>
    <div class="box"></div>
</body>
</html>
```

打开Chrome，F12，控制台显示：`Quirks Mode enabled`。那个蓝色方块的实际宽度不是 100px，而是...你用Elements面板测量，104px？不对，鼠标移动一下，变成了 108px。

"盒模型变了，"你低语。在标准模式下，`width: 100px` 指的是内容区域的宽度。但在怪异模式下，它包含了 padding 和 border。更糟的是，怪异模式下的盒模型计算方式在不同元素上还不一致。

你删掉Doctype之前的注释，刷新页面——`Standards Mode`。蓝色方块变成了精确的 100px。

"只是因为一个注释？"你难以置信。

上午十点,前端同事老王路过你的工位:"还在调那个客户问题?看起来挺棘手啊。"

"是Doctype的问题,"你说,"一个注释就能触发怪异模式。"

"啊对,我以前也遇到过,"老王点点头,"建议你把所有页面都检查一遍,确保Doctype都是第一行。"

你开始系统地测试Doctype的各种情况:

```html
<!-- 测试1：没有Doctype -->
<html>
...
```
结果：Quirks Mode

```html
<!-- 测试2：Doctype前有空格 -->

<!DOCTYPE html>
...
```
结果：Standards Mode（空格没问题）

```html
<!-- 测试3：Doctype前有注释 -->
<!-- 注释 -->
<!DOCTYPE html>
...
```
结果：Quirks Mode（注释会触发）

```html
<!-- 测试4：错误的Doctype -->
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html>
...
```
结果：Almost Standards Mode（几乎标准模式）

你打开MDN，查阅文档。原来浏览器有三种渲染模式：
- **Quirks Mode**（怪异模式）：模拟旧版浏览器的行为
- **Standards Mode**（标准模式）：按W3C标准渲染
- **Almost Standards Mode**（几乎标准模式）：除了表格单元格的高度，其他都按标准

浏览器如何判断使用哪种模式？它会检查HTML文档的开头，如果有有效的Doctype声明，就进入标准模式。如果没有，或者Doctype之前有内容（除了XML声明和BOM），就进入怪异模式。

你突然想起更多诡异的表现：客户说他们的布局在不同页面上表现不一致。你检查了网站的其他页面，发现有些页面的Doctype是：

```html
<!DOCTYPE html>
```

有些是：

```html
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
```

还有一个页面，根本没有Doctype。

三种不同的Doctype，触发了三种不同的渲染模式。用户在网站内部跳转时，布局不断变化。CSS的同一条规则，在不同页面上有不同的表现。

---

## 真相浮现

你创建了一个对比测试，清楚地展示了三种模式的差异：

```html
<!-- 怪异模式：没有Doctype -->
<html>
<head>
    <style>
        .box {
            width: 100px;
            padding: 10px;
            border: 5px solid black;
        }
    </style>
</head>
<body>
    <div class="box">怪异模式</div>
</body>
</html>
```

在怪异模式下，这个 `.box` 的实际渲染宽度是 100px（width包含了padding和border）。

```html
<!-- 标准模式：正确的Doctype -->
<!DOCTYPE html>
<html>
<head>
    <style>
        .box {
            width: 100px;
            padding: 10px;
            border: 5px solid black;
        }
    </style>
</head>
<body>
    <div class="box">标准模式</div>
</body>
</html>
```

在标准模式下，同样的CSS，实际渲染宽度是 130px（100 + 10×2 + 5×2）。

你测试了更多差异：

```javascript
// 在控制台检查当前模式
console.log(document.compatMode);
// "CSS1Compat" = 标准模式
// "BackCompat" = 怪异模式
```

你发现了一系列表现差异：

**怪异模式的特性**：
- 盒模型：width包含padding和border（类似 `box-sizing: border-box`）
- 表格字体：不继承body的字体设置
- 行内元素尺寸：可以设置width和height
- 百分比高度：即使父元素没有明确高度也会计算
- `img` 元素：底部有奇怪的空隙

你开始修复所有页面。最简单的方案就是统一使用HTML5的Doctype：

```html
<!DOCTYPE html>
```

这是最短、最简单、也是最现代的Doctype声明。确保它是文档的第一行，之前不能有任何内容（空格可以，但注释不行）。

你检查了整个项目的所有HTML文件，确保：
1. 每个文件第一行都是 `<!DOCTYPE html>`
2. Doctype之前没有注释
3. 没有使用过时的HTML4或XHTML的Doctype

下午一点,你在客户的环境上测试——所有页面表现一致,布局精确,CSS按预期工作。

你给产品经理发了条消息:"问题已解决,是Doctype声明位置的问题。已修复并验证。"

几分钟后,产品经理回复:"客户确认没问题了,辛苦了!记得写个文档,避免以后再出现这种情况。"

你靠在椅背上,长长地呼出一口气。一个看似简单的HTML声明,竟然能引发如此大的渲染差异。

---

## 世界法则

**世界规则 1：Doctype 决定渲染模式**

浏览器通过文档开头的Doctype声明来判断使用哪种渲染模式。这个决定会影响整个页面的CSS解析和DOM行为。

```javascript
// 检查当前文档的渲染模式
console.log(document.compatMode);
// "CSS1Compat" - 标准模式（Standards Mode）
// "BackCompat"  - 怪异模式（Quirks Mode）
```

---

**世界规则 2：三种渲染模式的触发条件**

- **标准模式**（Standards Mode）：有有效的HTML5 Doctype
  ```html
  <!DOCTYPE html>
  ```

- **怪异模式**（Quirks Mode）：没有Doctype，或者Doctype之前有内容（除了BOM和XML声明）
  ```html
  <!-- 注释会触发怪异模式 -->
  <!DOCTYPE html>
  ```
  或
  ```html
  <html>  <!-- 完全没有Doctype -->
  ```

- **几乎标准模式**（Almost Standards Mode）：使用旧版Doctype
  ```html
  <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
  ```

---

**世界规则 3：怪异模式的盒模型差异**

在怪异模式下，`width` 和 `height` 的含义改变：

```css
.box {
    width: 100px;
    padding: 10px;
    border: 5px solid black;
}
```

- **标准模式**：实际宽度 = 100 + 10×2 + 5×2 = 130px
- **怪异模式**：实际宽度 = 100px（padding和border包含在内）

怪异模式的盒模型类似于 `box-sizing: border-box`，但不完全相同且不可控。

---

**世界规则 4：Doctype 必须是文档第一行**

Doctype之前只能有：
- ✅ 空白字符（空格、换行）
- ✅ BOM（Byte Order Mark）
- ✅ XML声明（仅在XHTML中）
- ❌ 注释（会触发怪异模式）
- ❌ 任何其他内容

```html
<!-- ❌ 错误：注释在Doctype之前 -->
<!-- 这是注释 -->
<!DOCTYPE html>
<html>...</html>

<!-- ✅ 正确：Doctype在第一行 -->
<!DOCTYPE html>
<!-- 这里可以有注释 -->
<html>...</html>
```

---

**世界规则 5：现代网页统一使用 HTML5 Doctype**

HTML5的Doctype是最简洁、最现代的选择：

```html
<!DOCTYPE html>
```

不需要版本号、DTD URL或其他复杂声明。它：
- 向后兼容所有现代浏览器
- 触发标准模式
- 不区分大小写（`<!doctype html>` 也可以）
- 是所有新项目的推荐选择

---

**世界规则 6：不同模式下的其他差异**

除了盒模型，怪异模式还有其他行为差异：

```css
/* 怪异模式下 */
body { font-size: 16px; }
table { font-size: ???; }  /* 不继承body的字体大小 */

/* 怪异模式下 */
span {
    width: 100px;   /* 居然生效了（标准模式下无效） */
    height: 50px;
}
```

避免依赖这些差异，始终使用标准模式。

---

**事故档案编号**：DOM-2024-0802
**影响范围**：整个页面的CSS渲染和布局计算
**根本原因**：Doctype声明缺失或位置错误，触发怪异模式
**修复成本**：低（添加正确的Doctype声明）

这是DOM世界第2次被记录的模式裂痕事故。世界的裁决在文档打开的瞬间就已完成，之后的所有规则都将按照那个模式执行。选择你的模式，就是选择你的世界。
