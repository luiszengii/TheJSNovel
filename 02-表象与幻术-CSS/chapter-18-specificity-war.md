《第18次记录:权重战争事故 —— 样式冲突的裁决法庭》

---

## 事故现场

周五上午十点，你接手了一个遗留项目，需要修改按钮的背景色。办公室里很安静，大部分人都去参加技术分享会了。

你在CSS文件里找到了按钮的样式：

```css
.button {
    background: blue;
}
```

你把`blue`改成`red`，刷新页面——按钮还是蓝色。

"怎么会？"你眉头一皱。

上午十点半，前端组长发来消息："那个按钮样式改完了吗？下午要发版本。"

"在调，"你回复，心里有些烦躁。

你打开DevTools，看到`.button`的样式确实被应用了，但被另一个规则覆盖了：

```css
#submit-btn {
    background: blue;
}
```

"ID选择器优先级更高..."你删掉了`#submit-btn`规则，刷新页面——按钮还是蓝色。

你继续查找，发现了行内样式：

```html
<button class="button" id="submit-btn" style="background: blue;">提交</button>
```

你删掉行内样式，改CSS为red，终于生效了。但第二天，另一个开发者提交了代码：

```css
.form .button {
    background: blue !important;
}
```

你的red又被覆盖成blue了。你加上`!important`：

```css
.button {
    background: red !important;
}
```

但没用，对方的`.form .button`更具体。你继续增加权重：

```css
.form .button.primary {
    background: red !important;
}
```

这场权重战争开始失控...

---

## 深入迷雾

上午十一点，你决定彻底搞清楚CSS的权重计算规则。首先，你测试了最基本的情况：

```html
<p class="text" id="intro">测试文本</p>
```

```css
p { color: black; }           /* 元素选择器 */
.text { color: blue; }        /* 类选择器 */
#intro { color: red; }        /* ID选择器 */
```

结果：红色（ID选择器胜出）。

你测试了组合选择器：

```css
p { color: black; }                    /* 权重: 0,0,0,1 */
.text { color: blue; }                 /* 权重: 0,0,1,0 */
p.text { color: green; }               /* 权重: 0,0,1,1 */
#intro { color: red; }                 /* 权重: 0,1,0,0 */
div p { color: purple; }               /* 权重: 0,0,0,2 */
```

你意识到权重是分级计算的，不是简单的数字相加：

- 1个ID选择器（0,1,0,0）> 999个类选择器（0,0,999,0）
- 1个类选择器（0,0,1,0）> 999个元素选择器（0,0,0,999）

你测试了`!important`：

```css
.text { color: blue !important; }     /* 权重: ∞,0,0,1,0 */
#intro { color: red; }                /* 权重: 0,1,0,0 */
```

结果：蓝色。`!important`打破了正常的权重规则。

但当两个`!important`冲突时：

```css
.text { color: blue !important; }
#intro { color: red !important; }
```

结果：红色。`!important`之间还是按权重计算，ID > class。

你发现了`:not()`的特殊规则：

```css
p { color: black; }                    /* 0,0,0,1 */
:not(.exclude) { color: blue; }        /* 0,0,1,0 - :not()不计权重，但内部选择器计 */
```

---

## 真相浮现

中午十二点，你终于理清了CSS权重的完整计算规则。

你整理了CSS权重的完整计算规则：

**权重计算公式：(a, b, c, d)**

```
a = 行内样式（style属性）
b = ID选择器数量
c = 类选择器、属性选择器、伪类选择器数量
d = 元素选择器、伪元素选择器数量
```

**示例计算**：

```css
/* (0,0,0,1) */
p { }

/* (0,0,1,0) */
.text { }

/* (0,1,0,0) */
#intro { }

/* (1,0,0,0) */
<p style="..."> { }

/* (0,0,1,1) */
p.text { }

/* (0,1,1,0) */
#intro.text { }

/* (0,0,2,1) */
.container .text p { }

/* (0,1,1,2) */
div #intro.text p { }

/* (0,0,3,0) */
.nav .menu .item { }

/* (0,0,1,3) */
body div p.text { }
```

**权重对比规则**：

```javascript
// 比较两个权重 (a1,b1,c1,d1) vs (a2,b2,c2,d2)
// 从左到右依次比较，谁大谁胜

(1,0,0,0) > (0,999,999,999)  // 行内 > 任何选择器
(0,1,0,0) > (0,0,999,999)    // 1个ID > 999个class
(0,0,1,0) > (0,0,0,999)      // 1个class > 999个元素
```

你创建了完整的测试案例：

```html
<!DOCTYPE html>
<html>
<head>
    <title>CSS权重测试</title>
    <style>
        /* 权重: (0,0,0,1) */
        p {
            color: black;
        }

        /* 权重: (0,0,1,0) - 胜出 */
        .text {
            color: blue;
        }

        /* 权重: (0,1,0,0) - 胜出 */
        #intro {
            color: red;
        }

        /* 权重: (0,0,1,1) */
        p.text {
            color: green;
        }

        /* 权重: (0,0,2,1) */
        .container .text p {
            color: purple;
        }

        /* 权重: (0,1,1,1) - 最高 */
        div#intro.text p {
            color: orange;
        }

        /* !important 测试 */
        .important-test {
            color: blue !important;  /* 权重: ∞,0,0,1,0 */
        }

        #important-id {
            color: red;  /* 权重: 0,1,0,0 - 被!important覆盖 */
        }

        /* 伪类权重 */
        a:hover {
            color: red;  /* (0,0,1,1) */
        }

        a.link:hover {
            color: blue;  /* (0,0,2,1) - 胜出 */
        }
    </style>
</head>
<body>
    <div class="container">
        <p class="text" id="intro">
            权重测试文本 - 应该是什么颜色？
        </p>
    </div>

    <p class="important-test" id="important-id">
        !important 测试 - 应该是蓝色
    </p>

    <a href="#" class="link">悬停测试链接</a>

    <script>
        // 计算权重的工具函数
        function calculateSpecificity(selector) {
            const a = selector.includes('style=') ? 1 : 0;
            const b = (selector.match(/#/g) || []).length;
            const c = (selector.match(/\./g) || []).length +
                      (selector.match(/\[/g) || []).length +
                      (selector.match(/:/g) || []).length;
            const d = (selector.match(/[a-z]+/g) || []).length;

            return `(${a},${b},${c},${d})`;
        }

        // 测试示例
        console.log('p 权重:', calculateSpecificity('p'));
        console.log('.text 权重:', calculateSpecificity('.text'));
        console.log('#intro 权重:', calculateSpecificity('#intro'));
        console.log('p.text 权重:', calculateSpecificity('p.text'));
        console.log('div#intro.text p 权重:', calculateSpecificity('div#intro.text p'));

        // 获取实际应用的样式
        const p = document.querySelector('#intro');
        const computed = getComputedStyle(p);
        console.log('实际颜色:', computed.color);
    </script>
</body>
</html>
```

---

## 世界法则

**世界规则 1：CSS权重四级计分系统**

权重格式：`(a, b, c, d)`

```
a = 行内样式（1000分）
b = ID选择器（100分）
c = 类/属性/伪类选择器（10分）
d = 元素/伪元素选择器（1分）
```

**示例**：

```css
p { }                          /* (0,0,0,1) = 1分 */
.text { }                      /* (0,0,1,0) = 10分 */
#intro { }                     /* (0,1,0,0) = 100分 */
<p style="..."> { }            /* (1,0,0,0) = 1000分 */

p.text { }                     /* (0,0,1,1) = 11分 */
#intro.text { }                /* (0,1,1,0) = 110分 */
div p.text { }                 /* (0,0,1,2) = 12分 */
#nav .menu .item { }           /* (0,1,2,0) = 120分 */
```

**注意**：权重不是十进制数字，是分级比较：

```
(0,1,0,0) > (0,0,99,99)   ❌ 不是 100 vs 999
(0,1,0,0) 绝对大于 (0,0,X,X)  ✅ 分级胜出
```

---

**世界规则 2：权重比较规则 - 从左到右**

```
比较步骤：
1. 先比较 a（行内样式）
2. 如果相等，比较 b（ID数量）
3. 如果相等，比较 c（类/属性/伪类数量）
4. 如果相等，比较 d（元素数量）
5. 如果全部相等，后定义的覆盖先定义的
```

**示例**：

```css
/* 权重比较 */
(1,0,0,0) > (0,100,100,100)  /* 行内样式胜出 */
(0,2,0,0) > (0,1,100,100)    /* 2个ID > 1个ID */
(0,1,5,0) > (0,1,3,10)       /* 同1个ID，5个class > 3个class */
(0,0,1,10) > (0,0,1,5)       /* 同1个class，10个元素 > 5个元素 */
```

---

**世界规则 3：!important 改变一切**

```css
/* 普通权重 */
#intro { color: red; }           /* (0,1,0,0) */
.text { color: blue; }           /* (0,0,1,0) */
/* 结果：红色 */

/* 加上 !important */
#intro { color: red; }           /* (0,1,0,0) */
.text { color: blue !important; }/* (∞,0,0,1,0) */
/* 结果：蓝色 - !important 覆盖更高权重 */

/* 两个 !important 对比 */
#intro { color: red !important; }    /* (∞,0,1,0,0) */
.text { color: blue !important; }    /* (∞,0,0,1,0) */
/* 结果：红色 - !important 之间还是比权重 */
```

**!important 优先级**：

```
1. 行内 !important (最高)
2. ID !important
3. 类 !important
4. 元素 !important
5. 行内样式（无!important）
6. ID选择器（无!important）
7. 类选择器（无!important）
8. 元素选择器（无!important）
```

---

**世界规则 4：通配符和组合器不计权重**

```css
/* 通配符 * 权重为 0 */
* { }                    /* (0,0,0,0) */
*.text { }               /* (0,0,1,0) - 只计 .text */

/* 组合器不计权重 */
div > p { }              /* (0,0,0,2) - > 不计 */
h2 + p { }               /* (0,0,0,2) - + 不计 */
div ~ p { }              /* (0,0,0,2) - ~ 不计 */
div p { }                /* (0,0,0,2) - 空格不计 */
```

---

**世界规则 5：:not() 伪类特殊规则**

```css
/* :not() 本身不计权重，但内部选择器计入 */
:not(p) { }              /* (0,0,0,1) - 只计 p */
:not(.text) { }          /* (0,0,1,0) - 只计 .text */
:not(#intro) { }         /* (0,1,0,0) - 只计 #intro */

/* 对比 */
p:not(.exclude) { }      /* (0,0,1,1) - p + .exclude */
.text:not(#intro) { }    /* (0,1,1,0) - .text + #intro */
```

---

**世界规则 6：权重相同时，后定义覆盖先定义**

```css
/* 两个权重相同的规则 */
.text { color: blue; }   /* (0,0,1,0) */
.text { color: red; }    /* (0,0,1,0) */
/* 结果：红色 - 后定义的胜出 */

/* 不同位置的相同权重 */
/* a.css */
.button { background: blue; }

/* b.css */
.button { background: red; }

<link rel="stylesheet" href="a.css">
<link rel="stylesheet" href="b.css">
/* 结果：红色 - b.css 后加载 */
```

---

**世界规则 7：避免权重战争的最佳实践**

```css
/* ❌ 不推荐：过度依赖高权重 */
#header #nav .menu .item a { }  /* (0,2,2,1) - 过度具体 */
div div div p { }               /* (0,0,0,4) - 过深嵌套 */
.text { color: red !important; } /* 滥用 !important */

/* ✅ 推荐：使用合理的权重 */
.nav-link { }                   /* (0,0,1,0) - 单个类 */
.nav-link:hover { }             /* (0,0,2,0) - 添加状态 */
.nav-link.active { }            /* (0,0,2,0) - 添加修饰 */

/* ✅ BEM 命名法避免权重问题 */
.block { }
.block__element { }
.block__element--modifier { }
/* 所有选择器权重相同 (0,0,1,0) */
```

**最佳实践**：
1. 避免使用ID选择器做样式
2. 避免过深的选择器嵌套（≤3层）
3. 避免滥用`!important`
4. 使用BEM等命名规范保持权重一致
5. 按功能模块组织CSS，控制权重范围

**权重调试技巧**：

```javascript
// Chrome DevTools中查看权重
// Elements → Styles → 点击选择器旁的小箭头

// 计算权重工具
function getSpecificity(selector) {
    const a = 0;  // 行内样式通过元素检查
    const b = (selector.match(/#[a-z]/gi) || []).length;
    const c = (selector.match(/\.[a-z]|\[.*?\]|:[a-z]/gi) || []).length;
    const d = (selector.match(/^[a-z]|[\s>+~][a-z]/gi) || []).length;
    return [a, b, c, d];
}

console.log(getSpecificity('#nav .menu .item'));  // [0, 1, 2, 0]
```

下午一点，你用正确的权重规则重构了按钮样式："按钮样式已修复，移除了所有!important，使用合理的选择器权重。"

前端组长回复："太好了，准备发版本！"

你靠在椅背上，长长地呼出一口气。CSS权重战争，终于结束了。

---

**事故档案编号**：CSS-2024-1618
**影响范围**：样式冲突、权重计算、选择器设计
**根本原因**：不理解CSS权重分级系统和比较规则
**修复成本**：中等（需要重构选择器，移除过度依赖高权重的代码）

这是CSS世界第18次被记录的权重战争事故。CSS权重不是简单的数字游戏，而是分级裁决系统——1个ID永远大于999个class，1个class永远大于999个元素。当开发者不理解这个规则，就会陷入无休止的权重军备竞赛，用`!important`互相覆盖，用深层嵌套提升权重。真正的解决方案不是提升权重，而是设计合理的选择器架构。
