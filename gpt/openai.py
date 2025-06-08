import os
import openai
from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime

class OpenAIChatBot:
    def __init__(self, api_key=None):
        """
        初始化OpenAI聊天機器人
        
        Args:
            api_key: OpenAI API密鑰，如果沒有提供會從環境變量OPENAI_API_KEY中讀取
        """
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
        if not openai.api_key:
            raise ValueError("請設置OPENAI_API_KEY環境變量或提供api_key參數")
            
        self.conversation_history = []
        
    def add_message(self, role, content):
        """添加消息到對話歷史"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
    def get_response(self, user_input, system_prompt=None):
        """
        獲取OpenAI回應
        
        Args:
            user_input: 用戶輸入
            system_prompt: 系統提示詞（可選）
            
        Returns:
            AI回應的內容
        """
        try:
            # 構建消息列表
            messages = []
            
            # 添加系統提示詞
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 添加對話歷史（最近10條消息）
            recent_history = self.conversation_history[-10:]
            for msg in recent_history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # 添加當前用戶輸入
            messages.append({"role": "user", "content": user_input})
            
            # 調用OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # 保存對話歷史
            self.add_message("user", user_input)
            self.add_message("assistant", ai_response)
            
            return ai_response
            
        except Exception as e:
            error_msg = f"發生錯誤: {str(e)}"
            print(error_msg)
            return error_msg
    
    def clear_history(self):
        """清除對話歷史"""
        self.conversation_history = []
        
    def save_conversation(self, filename):
        """保存對話到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存對話失敗: {e}")
            return False
            
    def load_conversation(self, filename):
        """從文件加載對話"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.conversation_history = json.load(f)
            return True
        except Exception as e:
            print(f"加載對話失敗: {e}")
            return False

# Flask Web應用
app = Flask(__name__)
chatbot = None

@app.route('/')
def index():
    """主頁"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """處理聊天請求"""
    global chatbot
    
    if not chatbot:
        try:
            chatbot = OpenAIChatBot()
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    data = request.json
    user_input = data.get('message', '')
    system_prompt = data.get('system_prompt', '')
    
    if not user_input:
        return jsonify({'error': '請輸入消息'}), 400
    
    response = chatbot.get_response(user_input, system_prompt if system_prompt else None)
    
    return jsonify({
        'response': response,
        'conversation_history': chatbot.conversation_history
    })

@app.route('/clear', methods=['POST'])
def clear_conversation():
    """清除對話歷史"""
    global chatbot
    if chatbot:
        chatbot.clear_history()
    return jsonify({'message': '對話歷史已清除'})

@app.route('/save', methods=['POST'])
def save_conversation():
    """保存對話"""
    global chatbot
    if not chatbot:
        return jsonify({'error': '沒有對話可保存'}), 400
    
    filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    if chatbot.save_conversation(filename):
        return jsonify({'message': f'對話已保存到 {filename}'})
    else:
        return jsonify({'error': '保存失敗'}), 500

def run_cli():
    """命令行界面"""
    print("=== OpenAI 聊天機器人 ===")
    print("輸入 'quit' 退出，'clear' 清除歷史，'save' 保存對話")
    print("-" * 40)
    
    try:
        chatbot = OpenAIChatBot()
    except ValueError as e:
        print(f"初始化失敗: {e}")
        return
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            
            if user_input.lower() == 'quit':
                print("再見!")
                break
            elif user_input.lower() == 'clear':
                chatbot.clear_history()
                print("對話歷史已清除")
                continue
            elif user_input.lower() == 'save':
                filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                if chatbot.save_conversation(filename):
                    print(f"對話已保存到 {filename}")
                else:
                    print("保存失敗")
                continue
            elif not user_input:
                continue
            
            print("AI: ", end="", flush=True)
            response = chatbot.get_response(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n再見!")
            break
        except Exception as e:
            print(f"發生錯誤: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--web":
        # Web界面模式
        print("啟動Web界面...")
        print("打開瀏覽器訪問: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        # 命令行界面模式
        run_cli()
