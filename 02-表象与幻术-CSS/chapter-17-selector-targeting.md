《第17次记录:选择器失控事故 —— 规则的命中范围》

---

## 事故现场

周四上午九点，你接到紧急任务:给表格的奇数行添加灰色背景。办公室里有些嘈杂，运营团队在讨论新功能。

你快速写下CSS:

```css
tr {
    background: lightgray;
}
```

刷新页面——所有行都变成灰色了。

"我只想要奇数行..."你皱着眉头，想起了`:nth-child`,修改代码:

上午九点半，产品经理发来消息："表格样式调好了吗？十点要给客户演示。"

"在调，"你快速回复。

```css
tr:nth-child(odd) {
    background: lightgray;
}
```

刷新页面——结果更诡异了:第1行没有灰色,第2行有,第3行没有,第4行有...

"这是偶数行,不是奇数行!"你困惑地检查Elements面板,发现`<tr>`的父元素是`<tbody>`,而`<tbody>`的第一个子元素确实是第2个`<tr>`(因为第1个`<tr>`在`<thead>`里)。

你尝试了其他选择器,结果更混乱:

```css
table tr:first-child {
    /* 你以为这会选中表格的第一行 */
}
```

结果选中了`<thead>`里的第一个`<tr>`,`<tbody>`里的第一个`<tr>`,还有`<tfoot>`里的第一个`<tr>`——三行都被选中了。

"这个选择器到底选中了什么?"

---

## 深入迷雾

上午十点，你开始系统地测试选择器的行为。首先是最基础的元素选择器:

```html
<div class="box">
    <p>段落1</p>
    <p>段落2</p>
    <span>
        <p>段落3</p>
    </span>
</div>
```

```css
.box p {
    color: red;
}
```

结果:三个段落都变红了,包括`<span>`里的`<p>`。

"后代选择器会穿透所有层级..."

你测试了直接子选择器:

```css
.box > p {
    color: blue;
}
```

结果:只有段落1和段落2变蓝,段落3不受影响。

然后你测试了相邻兄弟选择器:

```html
<div>
    <h2>标题</h2>
    <p>段落1</p>
    <p>段落2</p>
</div>
```

```css
h2 + p {
    color: green;
}
```

结果:只有段落1变绿。

你改用通用兄弟选择器:

```css
h2 ~ p {
    color: green;
}
```

结果:段落1和段落2都变绿。

你测试了属性选择器的各种变体:

```html
<input type="text" name="username">
<input type="email" name="user-email">
<input type="password" name="password">
<div data-role="admin">管理员</div>
<div data-role="editor">编辑</div>
```

```css
/* 精确匹配 */
[type="text"] { border: 1px solid red; }

/* 包含单词 */
[name~="user"] { /* 不会匹配username */ }

/* 以...开头 */
[name^="user"] { border: 2px solid blue; }  /* 匹配username和user-email */

/* 以...结尾 */
[type$="word"] { border: 2px solid green; }  /* 匹配password */

/* 包含子串 */
[data-role*="min"] { color: red; }  /* 匹配admin */
```

你发现了伪类选择器的陷阱:

```html
<ul>
    <li class="item">项目1</li>
    <li class="item">项目2</li>
    <li>项目3</li>
    <li class="item">项目4</li>
</ul>
```

```css
.item:nth-child(2) {
    color: red;
}
```

结果:只有"项目2"变红(它既是`.item`又是第2个子元素)。

你尝试`:nth-of-type`:

```css
.item:nth-of-type(2) {
    color: blue;
}
```

结果:没有元素变蓝!`:nth-of-type`只看元素类型(`<li>`),不看class。

你终于找到了正确的方法——使用`:nth-child`配合class:

```css
li.item:nth-child(2) {
    /* 选中第2个子元素且是li.item */
}
```

---

## 真相浮现

上午十一点，你终于搞清楚了所有选择器的命中规则。

你整理了选择器的分类和优先级规则:

**基础选择器**:

```css
/* 1. 通配选择器 */
* { margin: 0; }

/* 2. 元素选择器 */
p { color: black; }

/* 3. 类选择器 */
.box { background: white; }

/* 4. ID选择器 */
#header { height: 60px; }

/* 5. 属性选择器 */
[type="text"] { border: 1px solid gray; }
```

**组合选择器**:

```css
/* 后代选择器 (空格) - 所有后代 */
.parent .child { }

/* 子选择器 (>) - 直接子元素 */
.parent > .child { }

/* 相邻兄弟选择器 (+) - 紧邻的下一个兄弟 */
h2 + p { }

/* 通用兄弟选择器 (~) - 之后的所有兄弟 */
h2 ~ p { }
```

**伪类选择器**:

```css
/* 状态伪类 */
a:link { }      /* 未访问 */
a:visited { }   /* 已访问 */
a:hover { }     /* 悬停 */
a:active { }    /* 激活 */
input:focus { } /* 聚焦 */
input:disabled { }  /* 禁用 */

/* 结构伪类 */
:first-child    /* 第一个子元素 */
:last-child     /* 最后一个子元素 */
:nth-child(n)   /* 第n个子元素 */
:nth-of-type(n) /* 第n个同类型元素 */
:only-child     /* 唯一子元素 */

/* 否定伪类 */
:not(.exclude)  /* 不包含指定选择器 */
```

你创建了完整的测试案例:

```html
<!DOCTYPE html>
<html>
<head>
    <title>选择器测试</title>
    <style>
        /* 测试1: 后代 vs 子选择器 */
        .test1 p { color: red; }          /* 所有后代p */
        .test2 > p { color: blue; }       /* 直接子p */

        /* 测试2: 相邻 vs 通用兄弟 */
        .test3 h3 + p { background: yellow; }    /* 紧邻的p */
        .test4 h3 ~ p { background: lightblue; } /* 所有后续p */

        /* 测试3: 属性选择器 */
        input[type="text"] { border: 2px solid red; }
        input[name^="user"] { border: 2px solid blue; }
        input[name$="mail"] { border: 2px solid green; }
        [data-role*="admin"] { font-weight: bold; }

        /* 测试4: nth-child vs nth-of-type */
        .test5 li:nth-child(odd) { background: lightgray; }
        .test6 li:nth-of-type(2n) { color: blue; }

        /* 测试5: 伪类组合 */
        .test7 a:not(:hover) { text-decoration: none; }
        .test8 input:focus:invalid { border-color: red; }
    </style>
</head>
<body>
    <h2>测试1: 后代选择器</h2>
    <div class="test1">
        <p>直接子元素p</p>
        <div>
            <p>嵌套的p</p>
        </div>
    </div>

    <h2>测试2: 子选择器</h2>
    <div class="test2">
        <p>直接子元素p (蓝色)</p>
        <div>
            <p>嵌套的p (不受影响)</p>
        </div>
    </div>

    <h2>测试3: 相邻兄弟</h2>
    <div class="test3">
        <h3>标题</h3>
        <p>紧邻的段落 (黄色)</p>
        <p>第二个段落 (不受影响)</p>
    </div>

    <h2>测试4: 通用兄弟</h2>
    <div class="test4">
        <h3>标题</h3>
        <p>第一个段落 (浅蓝)</p>
        <p>第二个段落 (浅蓝)</p>
    </div>

    <h2>测试5: 属性选择器</h2>
    <input type="text" name="username">
    <input type="email" name="user-mail">
    <input type="password" name="password">

    <h2>测试6: nth-child</h2>
    <ul class="test5">
        <li>项目1 (奇数,灰色)</li>
        <li>项目2</li>
        <li>项目3 (奇数,灰色)</li>
        <li>项目4</li>
    </ul>

    <script>
        // 查询选择器测试
        console.log('后代选择器:', document.querySelectorAll('.test1 p').length);  // 2
        console.log('子选择器:', document.querySelectorAll('.test2 > p').length);    // 1

        // 测试伪类
        const links = document.querySelectorAll('a:not([href])');
        console.log('无href的链接:', links.length);

        // 属性选择器
        const userInputs = document.querySelectorAll('[name^="user"]');
        console.log('以user开头的input:', userInputs.length);  // 2
    </script>
</body>
</html>
```

---

## 世界法则

**世界规则 1:选择器的六大类别**

```css
/* 1. 基础选择器 */
*               /* 通配选择器:所有元素 */
element         /* 元素选择器:特定标签 */
.class          /* 类选择器:特定class */
#id             /* ID选择器:特定id */

/* 2. 属性选择器 */
[attr]          /* 有此属性 */
[attr="value"]  /* 属性值精确匹配 */
[attr^="value"] /* 属性值以...开头 */
[attr$="value"] /* 属性值以...结尾 */
[attr*="value"] /* 属性值包含... */
[attr~="value"] /* 属性值包含完整单词 */

/* 3. 伪类选择器 */
:hover, :focus, :active    /* 状态伪类 */
:first-child, :last-child  /* 结构伪类 */
:nth-child(n)              /* 位置伪类 */
:not(selector)             /* 否定伪类 */

/* 4. 伪元素选择器 */
::before, ::after          /* 内容伪元素 */
::first-line, ::first-letter /* 文本伪元素 */

/* 5. 组合选择器 */
A B     /* 后代选择器 */
A > B   /* 子选择器 */
A + B   /* 相邻兄弟选择器 */
A ~ B   /* 通用兄弟选择器 */

/* 6. 分组选择器 */
A, B, C /* 多个选择器 */
```

---

**世界规则 2:后代选择器穿透所有层级**

```html
<div class="container">
    <p>层级1</p>
    <div>
        <p>层级2</p>
        <div>
            <p>层级3</p>
        </div>
    </div>
</div>
```

```css
/* 后代选择器:选中所有后代 */
.container p {
    color: red;
}
/* 结果:层级1、2、3全部变红 */

/* 子选择器:只选中直接子元素 */
.container > p {
    color: blue;
}
/* 结果:只有层级1变蓝 */
```

---

**世界规则 3:相邻兄弟 vs 通用兄弟**

```html
<div>
    <h2>标题</h2>
    <p>段落1</p>
    <p>段落2</p>
    <p>段落3</p>
</div>
```

```css
/* 相邻兄弟 (+): 紧邻的下一个兄弟 */
h2 + p {
    color: red;
}
/* 结果:只有段落1变红 */

/* 通用兄弟 (~): 之后的所有兄弟 */
h2 ~ p {
    color: blue;
}
/* 结果:段落1、2、3都变蓝 */
```

---

**世界规则 4:nth-child vs nth-of-type**

```html
<div>
    <p>段落1</p>
    <div>div1</div>
    <p>段落2</p>
    <p>段落3</p>
</div>
```

```css
/* nth-child: 按所有子元素计数 */
p:nth-child(2) {
    /* 选中div1位置的p → 无匹配 */
}

/* nth-of-type: 按同类型元素计数 */
p:nth-of-type(2) {
    /* 选中第2个p元素 → 段落2 */
}
```

**公式语法**:

```css
:nth-child(odd)      /* 奇数 */
:nth-child(even)     /* 偶数 */
:nth-child(3)        /* 第3个 */
:nth-child(2n)       /* 2的倍数 */
:nth-child(2n+1)     /* 2n+1: 1,3,5... */
:nth-child(3n)       /* 3的倍数: 3,6,9... */
:nth-child(-n+3)     /* 前3个 */
:nth-child(n+4)      /* 从第4个开始 */
```

---

**世界规则 5:属性选择器的七种匹配模式**

```css
/* 1. 存在匹配 */
[disabled] { }
/* 有disabled属性即可,不管值是什么 */

/* 2. 精确匹配 */
[type="text"] { }
/* 属性值必须完全等于"text" */

/* 3. 包含单词 */
[class~="active"] { }
/* class="btn active" 匹配 */
/* class="inactive" 不匹配 */

/* 4. 前缀匹配(带连字符) */
[lang|="en"] { }
/* lang="en" 或 lang="en-US" 匹配 */

/* 5. 开头匹配 */
[href^="https"] { }
/* href="https://..." 匹配 */

/* 6. 结尾匹配 */
[src$=".jpg"] { }
/* src="photo.jpg" 匹配 */

/* 7. 包含匹配 */
[class*="btn"] { }
/* class="my-btn-primary" 匹配 */
```

---

**世界规则 6:伪类的四种状态顺序(LVHA)**

```css
/* 链接状态必须按此顺序定义,否则会互相覆盖 */

a:link {
    /* 未访问的链接 */
}

a:visited {
    /* 已访问的链接 */
}

a:hover {
    /* 鼠标悬停 */
}

a:active {
    /* 鼠标按下 */
}

/* 记忆方法: LoVe HAte */
```

**原因**:
- 特异性相同时,后定义的覆盖先定义的
- `:visited`会覆盖`:link`
- `:hover`会覆盖`:visited`
- `:active`会覆盖`:hover`

---

**世界规则 7:选择器性能考虑**

```css
/* ❌ 低效:从右到左匹配,扫描所有a元素 */
#header nav ul li a { }

/* ✅ 高效:直接定位 */
.nav-link { }

/* ❌ 低效:通配符匹配所有元素 */
* { box-sizing: border-box; }

/* ✅ 较好:只应用于需要的元素 */
html { box-sizing: border-box; }
*, *::before, *::after {
    box-sizing: inherit;
}
```

**性能排序(快→慢)**:
1. ID选择器: `#header`
2. 类选择器: `.nav`
3. 元素选择器: `div`
4. 相邻选择器: `h2 + p`
5. 子选择器: `ul > li`
6. 后代选择器: `div p`
7. 通配选择器: `*`
8. 属性选择器: `[type="text"]`
9. 伪类选择器: `:hover`

**最佳实践**:
- 避免深层嵌套 (`a b c d e { }`)
- 使用类而不是元素选择器
- 避免通配符
- 浏览器从右向左匹配,最右边的选择器应该尽可能具体

上午十一点半，你把修复后的表格样式代码提交了："表格奇数行样式已修复，使用正确的选择器了。"

产品经理回复："完美，演示顺利通过！"

你靠在椅背上，松了一口气。选择器的命中规则，终于搞清楚了。

---

**事故档案编号**:CSS-2024-1617
**影响范围**:样式命中、元素定位、性能优化
**根本原因**:不理解选择器的匹配规则和作用范围
**修复成本**:低(理解规则后调整选择器)

这是CSS世界第17次被记录的选择器失控事故。选择器是CSS定位元素的语言——它不仅决定样式应用在哪里,还决定样式应用的性能。后代选择器会穿透所有层级,`:nth-child`看的是所有兄弟,`:nth-of-type`只看同类型元素。理解这些差异,就理解了CSS如何在茫茫DOM树中精确找到目标。
