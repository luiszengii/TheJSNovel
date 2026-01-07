#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import sys

def fix_punctuation_spacing(content):
    """只在叙述文本中添加英文标点后的空格,跳过代码块和行内代码"""
    lines = content.split('\n')
    result = []
    in_code_block = False
    
    for line in lines:
        # 检测代码块边界
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
            continue
        
        # 如果在代码块内,不做任何处理
        if in_code_block:
            result.append(line)
            continue
        
        # 处理行内代码:先保护,再处理,最后恢复
        inline_code_parts = []
        def save_inline_code(match):
            inline_code_parts.append(match.group(0))
            return f'__INLINE_CODE_{len(inline_code_parts)-1}__'
        
        # 保护行内代码(反引号包围的部分)
        line = re.sub(r'`[^`]+`', save_inline_code, line)
        
        # 在叙述文本中添加英文标点后的空格
        # 规则:英文标点后面如果紧跟字母/数字/中文,则添加空格
        line = re.sub(r',([a-zA-Z0-9一-龥])', r', \1', line)
        line = re.sub(r'\.([a-zA-Z一-龥])', r'. \1', line)  # 注意:不包括数字,避免破坏小数
        line = re.sub(r'!([a-zA-Z0-9一-龥])', r'! \1', line)
        line = re.sub(r'\?([a-zA-Z0-9一-龥])', r'? \1', line)
        line = re.sub(r':([a-zA-Z0-9一-龥])', r': \1', line)
        line = re.sub(r';([a-zA-Z0-9一-龥])', r'; \1', line)
        
        # 恢复行内代码
        for i, code in enumerate(inline_code_parts):
            line = line.replace(f'__INLINE_CODE_{i}__', code)
        
        result.append(line)
    
    return '\n'.join(result)

if __name__ == '__main__':
    filename = sys.argv[1]
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixed_content = fix_punctuation_spacing(content)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed {filename}")
