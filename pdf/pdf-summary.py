#!/usr/bin/env python3
import os
import argparse
import re
import shutil
import datetime
import logging
from pathlib import Path
import fitz  # PyMuPDF
import openai
from dotenv import load_dotenv
import time

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pdf_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 載入環境變數中的API密鑰
# Load API key from environment variables
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_text_from_pdf(pdf_path):
    """從PDF檔案中提取文字"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        # 提取所有文本
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        
        logger.info(f"成功從PDF中提取了文字內容")
        return text
    
    except Exception as e:
        logger.error(f"處理PDF檔案 {pdf_path} 時出錯: {e}")
        return ""

def analyze_academic_paper(text, model="gpt-4.1-mini"):
    """
    深度分析學術論文，提取關鍵信息和結論
    
    参数:
    text (str): 从PDF中提取的文本
    model (str): 要使用的OpenAI模型名称
    
    返回:
    str: 生成的深度分析文本
    """
    try:
        logger.info(f"使用模型 {model} 进行论文分析")
        system_prompt = """你是一位精通學術論文分析的AI助手，請對以下學術論文進行深度分析。提供以下內容：
1. 論文標題與作者（如有提供）
2. 研究背景與問題陳述（為什麼進行這項研究？研究目的是什麼？）
3. 研究方法詳述（使用了哪些方法？實驗設計如何？）
4. 主要發現與結果（實驗或分析得出了哪些結果？數據表明什麼？）
5. 核心創新點（這篇論文有哪些創新或突破？）
6. 結論與影響（研究結論是什麼？對該領域有何影響？）
7. 局限性與未來研究方向（作者提到的局限性？建議的未來研究？）
8. 關鍵術語與概念解釋（解釋論文中的專業術語和核心概念）
9. 總體評價（該研究的重要性、可靠性和創新性評估）
10. 參考文獻（從論文中提取關鍵參考文獻，並按以下標準格式列出）

請使用標準的Markdown格式，並遵循以下規則：
1. 使用 # 作為主標題，## 作為次級標題，### 作為第三級標題
2. 使用粗體（**文字**）來強調重要概念或術語
3. 使用列表格式呈現多點內容
4. 用 > 引用原文中的重要段落

對於數學公式：
- 將內聯公式置於單個美元符號之間：$E=mc^2$
- 將獨立公式置於雙美元符號之間：$$\\sum_{i=1}^{n} x_i = x_1 + x_2 + \\ldots + x_n$$
- 確保所有數學符號都使用正確的LaTeX語法，例如：$\\alpha$, $\\beta$, $\\sum$, $\\int$, $\\frac{a}{b}$
- 複雜的數學表達式請使用標準LaTeX環境：$$\\begin{equation} ... \\end{equation}$$

參考文獻格式要求：
對於最重要的參考文獻（至少5-10個），使用以下格式：
1. Author1, Author2, and Author3. "Title of the Paper," _Journal or Conference Name_, pp. xx-xx, Year. [DOI/URL if available]

請提供詳盡的分析，讓讀者無需閱讀原論文即可全面理解。"""

        # 检查文本长度，如果太长，只取前部分
        if len(text) > 100000:
            logger.warning(f"文本过长 ({len(text)} 字符)，将截断至 100000 字符")
            text = text[:100000]
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"以下是學術論文的內容，請進行深度分析:\n\n{text}"}
        ]
        
        # 添加超时和重试机制
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                logger.info(f"尝试调用OpenAI API进行论文分析 (尝试 {retry_count + 1}/{max_retries})")
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=4000,
                    timeout=60  # 60秒超时
                )
                
                return response.choices[0].message.content
            except Exception as api_error:
                retry_count += 1
                logger.warning(f"API调用失败 (尝试 {retry_count}/{max_retries}): {api_error}")
                
                if retry_count >= max_retries:
                    logger.error(f"在 {max_retries} 次尝试后API调用仍然失败")
                    break
                    
                # 指数退避策略
                wait_time = 2 ** retry_count
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        return "分析失败。请稍后再试或联系管理员。"
    except Exception as e:
        logger.error(f"論文分析時出錯: {e}", exc_info=True)
        return "分析失敗。錯誤: " + str(e)

def extract_complete_key_sections(text, model="gpt-4.1-mini"):
    """
    提取論文中的完整關鍵章節內容
    
    参数:
    text (str): 从PDF中提取的文本
    model (str): 要使用的OpenAI模型名称
    
    返回:
    str: 提取的关键章节内容
    """
    try:
        logger.info(f"使用模型 {model} 提取论文关键章节")
        
        # 检查文本长度，如果太长，只取前部分
        if len(text) > 100000:
            logger.warning(f"文本过长 ({len(text)} 字符)，将截断至 100000 字符")
            text = text[:100000]
            
        system_content = """你是一位學術論文分析專家。你的任務是識別並提取學術論文中的所有關鍵章節（包括但不限於：摘要、引言、文獻綜述、研究方法、數據來源、實驗設計、結果分析、討論、結論、未來展望等）。

對於每個章節：
1. 提供章節標題和在論文中的確切位置
2. 完整提取章節的原始內容（不要簡化或縮短）
3. 保留所有關鍵數據、公式、引用和細節
4. 對於技術性或專業性較強的部分，提供必要的解釋說明
5. 標註出該章節中特別重要的發現、主張或結論

在Markdown格式上：
1. 使用 ## 作為章節標題
2. 使用 ### 作為章節內的子標題
3. 使用 > 區塊引用來標示原文直接引用
4. 使用粗體（**文字**）來標記重要概念
5. 使用 --- 分隔各個章節

對於數學公式和特殊符號：
- 內聯公式應使用單一美元符號包裹：$E=mc^2$
- 獨立的複雜公式應使用雙美元符號：$$\\frac{1}{n}\\sum_{i=1}^{n}x_i$$
- 避免使用不標準的符號表示法，確保準確使用LaTeX表示法
- 確保使用正確的反斜線：$\\alpha$ 而非 $\alpha$（後者在Markdown中可能顯示錯誤）
- 複雜公式可使用標準環境：$$\\begin{equation} ... \\end{equation}$$

目標是讓讀者通過閱讀你的提取，獲得與閱讀原文相同程度的學術價值和信息量，同時確保在Markdown中正確顯示所有內容。"""
            
        # 添加超时和重试机制
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                logger.info(f"尝试调用OpenAI API提取关键章节 (尝试 {retry_count + 1}/{max_retries})")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": f"請提取以下學術論文的完整關鍵章節內容:\n\n{text}"}
                    ],
                    temperature=0.1,
                    max_tokens=10000,
                    timeout=90  # 90秒超时
                )
                return response.choices[0].message.content
            except Exception as api_error:
                retry_count += 1
                logger.warning(f"API调用失败 (尝试 {retry_count}/{max_retries}): {api_error}")
                
                if retry_count >= max_retries:
                    logger.error(f"在 {max_retries} 次尝试后API调用仍然失败")
                    break
                    
                # 指数退避策略
                wait_time = 2 ** retry_count
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        return "章节提取失败。请稍后再试或联系管理员。"
    except Exception as e:
        logger.error(f"提取完整關鍵章節時出錯: {e}", exc_info=True)
        return "章節提取失敗。"

def fix_latex_symbols(text):
    """
    修复LaTeX符号问题，确保它们能在Markdown中正确显示
    
    参数:
    text (str): 需要处理的文本
    
    返回:
    str: 修复后的文本
    """
    if not text:
        return text
        
    # 修复常见的错误LaTeX符号用法
    common_word_fixes = [
        # 修复常见的单词错误
        (r'tw\$\\in\$in', r'twin'),
        (r'contro\$\\ll\$llrs', r'controllers'),
        (r'Dig\$?ital\s+T[wv]\$\\in\$in', r'Digital Twin'),
        (r'T[wv]\$\\in\$in', r'Twin'),
        (r'Spa\$\\in\$in', r'Spain'),
        (r'Network\$\\in\$in', r'Networking'),
        (r'Teleco\$\\\\mu\$muicacions', r'Telecommunications'),
        (r'M\$\\in\$innet', r'Mininet'),
        (r'Conta\$\\in\$inrlab', r'Containerlab'),
        (r'A\$\\ll\$lln', r'Allan'),
        (r'Case\$\\ll\$lls', r'Casells'),
        # 常见符号修复
        (r'\$\\in\$in', r'in'),
        (r'\$\\ll\$ll', r'll'),
        (r'\$\\\\mu\$mu', r'mu'),
        # 修复其他常见的LaTeX符号错误
        (r'\$\\alpha\$lpha', r'alpha'),
        (r'\$\\beta\$beta', r'beta'),
        (r'\$\\theta\$theta', r'theta'),
        (r'\$\\delta\$delta', r'delta'),
        (r'\$\\gamma\$gamma', r'gamma'),
        (r'\$\\lambda\$lambda', r'lambda'),
        (r'\$\\sigma\$sigma', r'sigma'),
        (r'\$\\omega\$omega', r'omega'),
        (r'\$\\pi\$pi', r'pi'),
        # 更多常见错误修复
        (r'\$\\chi\$chi', r'chi'),
        (r'\$\\tau\$tau', r'tau'),
        (r'\$\\eta\$eta', r'eta'),
        (r'\$\\epsilon\$epsilon', r'epsilon'),
        (r'\$\\rho\$rho', r'rho'),
        (r'\$\\phi\$phi', r'phi'),
        (r'\$\\xi\$xi', r'xi'),
        (r'\$\\nu\$nu', r'nu'),
        (r'Com\$\\mu\$mu', r'Commu'),
        (r'com\$\\mu\$mu', r'commu'),
        (r'Telecom\$\\mu\$mu', r'Telecommu'),
        (r'telecom\$\\mu\$mu', r'telecommu')
    ]
    
    # 应用特定修复
    processed_text = text
    for pattern, replacement in common_word_fixes:
        try:
            processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
        except Exception as e:
            logger.warning(f"正则表达式替换出错：{pattern} -> {replacement}，错误：{e}")
            # 继续处理其他模式，不中断整个过程
            continue
    
    # 处理数学环境，确保LaTeX环境正确包含在$$中
    environments = ['equation', 'align', 'gather', 'matrix', 'cases', 'bmatrix', 'pmatrix']
    for env in environments:
        try:
            # 将环境包裹在$$中，注意转义大括号
            processed_text = re.sub(
                r'\\begin\{' + env + r'\}(.*?)\\end\{' + env + r'\}',
                r'$$\\begin{' + env + r'}\1\\end{' + env + r'}$$',
                processed_text,
                flags=re.DOTALL
            )
        except Exception as e:
            logger.warning(f"处理数学环境 {env} 时出错：{e}")
            # 继续处理其他环境
            continue
    
    # 确保不会出现连续的 $$$$（连续出现的$$替换为单个$$）
    processed_text = re.sub(r'\${2,}', r'$$', processed_text)
    
    # 修复一些常见的行内公式错误
    processed_text = re.sub(r'\$([^$]+?)\$\s*\1', r'$\1$', processed_text)
    
    # 修复其他常见错误
    # 1. 错误的希腊字母表示
    greek_letters = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 
                     'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 'rho', 
                     'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega']
    for letter in greek_letters:
        try:
            # 修复形如 "\alpa" (少一个字母) 的错误
            processed_text = re.sub(r'\\' + letter[0] + letter[2:] + r'(?!\w)', r'\\' + letter, processed_text)
            # 修复形如 "\alphaa" (多一个字母) 的错误
            processed_text = re.sub(r'\\' + letter + letter[-1] + r'(?!\w)', r'\\' + letter, processed_text)
        except Exception as e:
            logger.warning(f"处理希腊字母 {letter} 时出错：{e}")
            continue
    
    # 2. 修复连续出现的相同公式
    processed_text = re.sub(r'\$([^$]+?)\$\s*\$\1\$', r'$\1$', processed_text)
    
    # 3. 修复缺少空格的公式表示
    processed_text = re.sub(r'(\w)\$', r'\1 $', processed_text)
    processed_text = re.sub(r'\$(\w)', r'$ \1', processed_text)
    
    return processed_text

def fix_bold_text(text):
    """
    修复粗体文本格式问题
    
    参数:
    text (str): 需要处理的文本
    
    返回:
    str: 修复后的文本
    """
    if not text:
        return text
        
    try:
        # 1. 修复格式错误的粗体标记：* * text * * -> **text**
        processed_text = re.sub(r'\*\s*\*\s+([^*]+?)\s+\*\s*\*', r'**\1**', text)
        
        # 2. 修复不对称的粗体标记：** text * -> **text**
        processed_text = re.sub(r'\*\*\s+([^*]+?)\s+\*(?!\*)', r'**\1**', processed_text)
        processed_text = re.sub(r'\*(?!\*)\s+([^*]+?)\s+\*\*', r'**\1**', processed_text)
        
        # 3. 移除粗体标记周围的多余空格：** text ** -> **text**
        processed_text = re.sub(r'\*\*\s+([^*]+?)\s+\*\*', r'**\1**', processed_text)
        
        # 4. 修复脱离的星号（单独的*）
        processed_text = re.sub(r'(?<!\*)\*(?!\*)\s', r'', processed_text)
        
        return processed_text
    except Exception as e:
        logger.warning(f"修复粗体文本时出错：{e}")
        return text  # 出错时返回原始文本

def fix_headers(text):
    """
    修复Markdown标题格式
    
    参数:
    text (str): 需要处理的文本
    
    返回:
    str: 修复后的文本
    """
    if not text:
        return text
        
    try:
        # 确保标题格式正确（#后有空格）
        processed_text = re.sub(r'^(#+)([^\s#])', r'\1 \2', text, flags=re.MULTILINE)
        
        # 修复多余空格的标题：# # Title -> # Title
        processed_text = re.sub(r'^(#+)(\s+#+\s)', r'\1 ', processed_text, flags=re.MULTILINE)
        
        return processed_text
    except Exception as e:
        logger.warning(f"修复标题时出错：{e}")
        return text

def fix_lists(text):
    """
    修复Markdown列表格式问题
    
    参数:
    text (str): 需要处理的文本
    
    返回:
    str: 修复后的文本
    """
    if not text:
        return text
        
    try:
        # 确保列表项后有空格
        processed_text = re.sub(r'^(\s*[-*+])([^\s])', r'\1 \2', text, flags=re.MULTILINE)
        
        # 修复数字列表格式
        processed_text = re.sub(r'^(\s*\d+\.)([^\s])', r'\1 \2', processed_text, flags=re.MULTILINE)
        
        return processed_text
    except Exception as e:
        logger.warning(f"修复列表时出错：{e}")
        return text

def process_markdown(text):
    """
    处理Markdown文本，修复各种格式问题
    
    参数:
    text (str): 需要处理的Markdown文本
    
    返回:
    str: 处理后的Markdown文本
    """
    if not text:
        return text
        
    try:
        # 修复LaTeX符号问题
        processed_text = fix_latex_symbols(text)
        
        # 修复粗体格式
        processed_text = fix_bold_text(processed_text)
        
        # 修复标题格式
        processed_text = fix_headers(processed_text)
        
        # 修复列表格式
        processed_text = fix_lists(processed_text)
        
        return processed_text
    except Exception as e:
        logger.error(f"处理Markdown文本时出错：{e}")
        # 如果处理失败，返回原始文本
        return text

def process_pdfs(model="gpt-4.1-mini"):
    """處理journals資料夾中的所有PDF檔案並生成深度分析"""
    # 設定固定的journals資料夾路徑
    input_dir = "journals"
    input_path = Path(input_dir)
    
    if not input_path.exists() or not input_path.is_dir():
        logger.error(f"輸入目錄 {input_dir} 不存在或不是一個目錄")
        return
    
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"在目錄 {input_dir} 中沒有找到PDF檔案")
        return
    
    # 創建輸出目錄
    output_dir = input_path / "analyses"
    output_dir.mkdir(exist_ok=True)
    
    # 創建已處理PDF的存放目錄
    done_dir = input_path / "done"
    done_dir.mkdir(exist_ok=True)
    
    logger.info(f"找到 {len(pdf_files)} 個PDF檔案，開始處理...")
    
    # 獲取當前日期並格式化為YYYYMMDD
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    
    # 處理每個PDF檔案
    for pdf_file in pdf_files:
        logger.info(f"處理檔案: {pdf_file.name}")
        text = extract_text_from_pdf(pdf_file)
        
        if not text:
            logger.warning(f"無法從 {pdf_file.name} 提取文字，跳過...")
            continue
        
        # 創建論文專屬目錄，前面加上日期
        folder_name = f"{current_date}_{pdf_file.stem}"
        paper_dir = output_dir / folder_name
        paper_dir.mkdir(exist_ok=True)
        
        # 1. 論文整體深度分析
        logger.info(f"正在生成 {pdf_file.name} 的深度分析...")
        analysis = analyze_academic_paper(text, model)
        
        # 處理分析內容的格式問題
        processed_analysis = process_markdown(analysis)
        
        # 添加参考文献部分（如果不存在）
        if "## 10. 參考文獻" not in processed_analysis and "## 參考文獻" not in processed_analysis:
            processed_analysis += "\n\n## 10. 參考文獻\n\n"
            processed_analysis += "本部分列出論文中引用的主要參考文獻。\n\n"
            
        analysis_file = paper_dir / "detailed_analysis.md"
        with open(analysis_file, "w", encoding="utf-8") as f:
            f.write(f"# {pdf_file.name} 深度分析\n\n")
            f.write(processed_analysis)
            
            # 添加Markdown查看器提醒
            f.write("\n\n---\n\n")
            f.write("> **注意**：本文檔包含數學公式，請使用支持LaTeX數學渲染的Markdown查看器（如VS Code + Markdown Math插件、Typora、JupyterLab等）以獲得最佳顯示效果。")
        
        logger.info(f"深度分析已保存至 {analysis_file}")
        
        # 2. 提取完整關鍵章節
        logger.info(f"正在提取 {pdf_file.name} 的完整關鍵章節...")
        complete_sections = extract_complete_key_sections(text, model)
        
        # 處理章節內容的格式問題
        processed_sections = process_markdown(complete_sections)
        
        sections_file = paper_dir / "complete_sections.md"
        with open(sections_file, "w", encoding="utf-8") as f:
            f.write(f"# {pdf_file.name} 完整關鍵章節\n\n")
            f.write(processed_sections)
            
            # 添加Markdown查看器提醒
            f.write("\n\n---\n\n")
            f.write("> **注意**：本文檔包含數學公式，請使用支持LaTeX數學渲染的Markdown查看器（如VS Code + Markdown Math插件、Typora、JupyterLab等）以獲得最佳顯示效果。")
        
        logger.info(f"完整關鍵章節已保存至 {sections_file}")
        
        # 創建README.md
        readme_file = paper_dir / "README.md"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(f"# {pdf_file.name} 分析報告\n\n")
            f.write(f"## 分析日期: {current_date}\n\n")
            f.write("## 分析內容\n\n")
            f.write("1. [詳細論文分析](detailed_analysis.md) - 包含論文主要觀點、方法、結果和結論的深度分析\n")
            f.write("2. [完整關鍵章節](complete_sections.md) - 提取論文的完整關鍵章節內容\n")
            
            f.write("\n## 說明\n\n")
            f.write("* 數學公式使用LaTeX格式，在支持Markdown的查看器中應能正確顯示\n")
            f.write("* 為獲得最佳顯示效果，請使用以下工具查看報告：\n")
            f.write("  * **VS Code** 安裝 Markdown All in One 和 Markdown+Math 插件\n")
            f.write("  * **Typora** - 專業Markdown編輯器，支持數學公式渲染\n")
            f.write("  * **JupyterLab** - 科學計算平台，支持完整LaTeX數學顯示\n")
        
        logger.info(f"{pdf_file.name} 處理完成。結果保存在 {paper_dir}")
        
        # 將處理完的PDF文件移動到done目錄
        done_file = done_dir / pdf_file.name
        try:
            shutil.move(str(pdf_file), str(done_file))
            logger.info(f"已將 {pdf_file.name} 移動到 {done_dir}")
        except Exception as move_err:
            logger.error(f"移動文件時出錯: {move_err}")
            # 如果移動失敗，嘗試複製
            try:
                shutil.copy2(str(pdf_file), str(done_file))
                os.remove(str(pdf_file))
                logger.info(f"已將 {pdf_file.name} 複製到 {done_dir} 並刪除原文件")
            except Exception as copy_err:
                logger.error(f"複製文件時出錯: {copy_err}")
                logger.warning(f"警告: 無法移動或複製 {pdf_file.name} 到 {done_dir}")
    
    logger.info("所有PDF文件處理完成。")

def main():
    parser = argparse.ArgumentParser(description="PDF學術論文深度分析工具")
    parser.add_argument("-m", "--model", default="gpt-4.1-mini", help="使用的OpenAI模型")
    
    args = parser.parse_args()
    
    # 確保設置了API密鑰
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("錯誤: 未設置OpenAI API密鑰。請在.env檔案中設置OPENAI_API_KEY環境變數。")
        return
    
    process_pdfs(args.model)

if __name__ == "__main__":
    main()
