import streamlit as st

st.markdown('''
# Regex for Filter Novel Titles

Three Minutes to Give You a Rough Idea of How to Use Regular
Expressions to Filter Novel Titles... Roughly?

Detailed tutorials on regular expressions are readily available on the
internet, but if you just need to know which regular expressions filter
out which novel chapter titles, you can look here.

## `第.*章`

This expression can match the following:

```
第一章 開始
第三十三章 你想不到吧
第022章 結局
```

In other words, as long as the line contains `第` and `章`
appears sequentially, it can be matched.

## `第\\d*章`

This expression can match the following:
```
第1章 開始
第2345章 你想不到吧
第022章 結局
```

But if there are any non-numeric characters in between,
it won't match. For example, the following cannot be matched:

```
第一章 開始
第三十三章 你想不到吧
```

''')
