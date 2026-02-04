"""
豆包大模型API服务
"""
import httpx
import base64
import os
from typing import List, Dict, Any, Tuple, Optional
from io import BytesIO
from PIL import Image

def _get_settings():
    """动态获取settings，支持测试模式"""
    try:
        from config import settings
        return settings
    except ImportError:
        # 测试模式下，config可能被替换为test_config
        import sys
        if 'config' in sys.modules:
            from config import settings
            return settings
        else:
            # 如果config模块不存在，尝试导入test_config
            from test_config import settings
            return settings

class DoubaoAPI:
    def __init__(self):
        settings = _get_settings()
        self.api_key = settings.DOUBAO_API_KEY
        self.api_url = settings.DOUBAO_API_URL
        self.model = settings.DOUBAO_MODEL
        
    def _encode_image(self, image_path: str) -> str:
        """将图片编码为base64"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def _prepare_images(self, image_urls: List[str]) -> List[Dict]:
        """准备图片消息"""
        image_messages = []
        for image_url in image_urls:
            # 如果是base64编码的图片，直接使用
            if image_url.startswith('data:image'):
                image_messages.append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })
            else:
                # 如果是文件路径，需要读取并编码
                try:
                    with open(image_url, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                        image_messages.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        })
                except Exception as e:
                    print(f"Error reading image {image_url}: {e}")
                    continue
        return image_messages
    
    def analyze_friend_circle(
        self,
        image_urls: List[str],
        supplementary_info: Dict[str, Any] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        分析朋友圈截图
        
        Args:
            image_urls: 图片URL列表（可能是本地路径或HTTP URL）
            supplementary_info: 补充信息（性别、年龄等）
        
        Returns:
            分析结果字典
        """
        # 构建Prompt
        prompt = self._build_prompt(supplementary_info)
        
        # 将图片转换为 base64 编码（因为火山引擎 API 无法访问 localhost）
        # 如果是本地路径，读取文件并编码为 base64
        input_content: List[Dict[str, Any]] = []
        for image_url in image_urls:
            # 如果是本地文件路径（不以 http:// 或 https:// 开头），转换为 base64
            if not image_url.startswith(('http://', 'https://', 'data:')):
                # 读取本地图片文件并编码为 base64
                try:
                    # 处理路径：uploads/1/xxx.jpg 或绝对路径
                    if image_url.startswith('uploads/'):
                        filepath = image_url
                    elif os.path.isabs(image_url):
                        filepath = image_url
                    else:
                        filepath = image_url
                    
                    # 读取并压缩图片（减少 base64 数据量）
                    with open(filepath, 'rb') as f:
                        original_data = f.read()
                    
                    # 压缩图片：最大宽度 1024px，质量 85%
                    try:
                        img = Image.open(BytesIO(original_data))
                        # 转换为 RGB（如果是 RGBA）
                        if img.mode in ('RGBA', 'LA', 'P'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = background
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # 调整大小：最大宽度 1024px，保持比例
                        max_width = 1024
                        if img.width > max_width:
                            ratio = max_width / img.width
                            new_height = int(img.height * ratio)
                            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                        
                        # 压缩为 JPEG
                        output = BytesIO()
                        img.save(output, format='JPEG', quality=85, optimize=True)
                        compressed_data = output.getvalue()
                        
                        # 编码为 base64
                        image_data = base64.b64encode(compressed_data).decode('utf-8')
                        mime_type = 'image/jpeg'
                        
                        print(f"[DEBUG] 图片压缩: {len(original_data)} -> {len(compressed_data)} bytes")
                    except Exception as e:
                        # 如果压缩失败，使用原始图片
                        print(f"[DEBUG] 图片压缩失败，使用原始图片: {e}")
                        image_data = base64.b64encode(original_data).decode('utf-8')
                        ext = os.path.splitext(filepath)[1].lower()
                        mime_type = {
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.png': 'image/png',
                            '.webp': 'image/webp'
                        }.get(ext, 'image/jpeg')
                    
                    # 使用 base64 data URL 格式
                    full_url = f"data:{mime_type};base64,{image_data}"
                except Exception as e:
                    print(f"读取图片文件失败 {image_url}: {e}")
                    raise Exception(f"无法读取图片文件: {image_url}")
            else:
                # 已经是 HTTP URL 或 data URL，直接使用
                full_url = image_url
            
            # 按照用户的curl示例格式：{"type": "input_image", "image_url": "..."}
            input_content.append({
                "type": "input_image",
                "image_url": full_url
            })
        
        # 添加文本内容
        input_content.append({
            "type": "input_text",
            "text": prompt
        })

        # 按照用户的curl示例格式构建payload
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": input_content
                }
            ],
            "max_output_tokens": 12000,
            "temperature": 0.8,
        }
        
        # 调用API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # 打印调试信息
            api_endpoint = f"{self.api_url}/responses"
            print(f"[DEBUG] API URL: {api_endpoint}")
            print(f"[DEBUG] Model: {self.model}")
            print(f"[DEBUG] Payload keys: {list(payload.keys())}")
            print(f"[DEBUG] Input content count: {len(input_content)}")
            
            # 增加超时时间：图片转base64和API调用需要较长时间
            with httpx.Client(timeout=300.0) as client:
                response = client.post(
                    api_endpoint,
                    json=payload,
                    headers=headers
                )
                
                # 打印响应状态
                print(f"[DEBUG] Response status: {response.status_code}")
                print(f"[DEBUG] Response headers: {dict(response.headers)}")
                
                if response.status_code != 200:
                    # 打印错误响应内容
                    try:
                        error_body = response.text
                        print(f"[DEBUG] Error response body: {error_body[:500]}")
                    except:
                        pass
                
                response.raise_for_status()
                result = response.json()
                usage = result.get("usage") or {}

                # 解析返回结果文本（responses 格式）
                analysis_text = self._extract_responses_output_text(result)
                
                # 打印调试信息：查看豆包返回的原始文本
                print(f"[DEBUG] 豆包返回的原始文本长度: {len(analysis_text)}")
                print(f"[DEBUG] 豆包返回的原始文本前500字符: {analysis_text[:500]}")
                
                # 解析分析结果（确保返回前端需要的固定结构）
                analysis_data = self._parse_analysis_result(analysis_text)
                
                # 打印调试信息：查看解析后的结果
                print(f"[DEBUG] 解析后的 match_score: {analysis_data.get('match_score')}")
                print(f"[DEBUG] 解析后的 personality 长度: {len(str(analysis_data.get('personality', '')))}")
                
                return analysis_data, usage
                
        except httpx.HTTPError as e:
            print(f"API调用失败: {e}")
            raise Exception(f"API调用失败: {str(e)}")
        except Exception as e:
            print(f"分析失败: {e}")
            raise Exception(f"分析失败: {str(e)}")
    
    def _build_prompt(self, supplementary_info: Dict[str, Any] = None) -> str:
        """构建分析Prompt"""
        base_prompt = """你是一位资深的心理学专家和情感咨询师，拥有超过10年的实战经验。你擅长通过细节洞察人性，能够从朋友圈的蛛丝马迹中挖掘出深层心理特征、情感需求和潜在动机。你的分析总是深入、具体、有洞察力，能够提供可操作的策略建议。

请仔细分析这些朋友圈截图，进行**深度、全面、有洞察力**的分析。要求：

## 分析要求（必须深入且具体）

### 1. **性格特征分析**（200-300字）
- 不仅要判断外向/内向，还要分析：社交模式、情绪表达方式、决策风格、压力应对机制
- 从朋友圈内容推断：是否喜欢分享、分享的频率和内容类型、互动方式
- 分析深层性格：是否有控制欲、是否敏感、是否缺乏安全感、是否追求完美
- **必须提供具体证据**：例如"从她频繁分享旅行照片可以看出..."、"她很少发负面情绪，说明..."

### 2. **兴趣爱好分析**（150-200字）
- 不仅要列出爱好，还要分析：为什么喜欢这些、这些爱好反映什么心理需求
- 分析爱好的深度：是浅尝辄止还是深度投入、是否有专业水平
- 从爱好推断：生活态度、消费能力、社交圈层、时间分配
- **提供具体建议**：如何通过共同爱好建立联系

### 3. **价值观倾向分析**（200-300字）
- 深入分析：人生目标、对成功的定义、对关系的期待、对未来的规划
- 从内容推断：是否重视家庭、是否追求事业、是否注重精神层面
- 分析消费观：是否理性消费、是否追求品质、是否愿意为体验付费
- 分析人生态度：是积极乐观还是消极悲观、是否有明确规划
- **必须结合具体内容**：例如"从她分享的XX可以看出她认为..."

### 4. **情感状态推测**（200-300字）
- 不仅要判断单身/恋爱，还要分析：情感需求、对关系的期待、是否容易接近
- 从细节推断：是否有情感创伤、是否在寻找什么、是否对感情有防备
- 分析情感成熟度：是否懂得经营关系、是否能够沟通、是否有情感智慧
- **提供具体证据**：例如"她朋友圈中XX内容暗示..."、"她的互动方式表明..."

### 5. **沟通建议**（必须非常具体）
- **推荐话题**（5-8个）：不仅要列出话题，还要说明为什么这些话题合适、如何自然引入、如何深入展开
- **开场白建议**（3-5个版本）：要针对不同场景（初次联系、日常聊天、深入交流），每个都要有具体话术
- **聊天技巧**（300-400字）：详细说明如何回应、如何引导话题、如何建立共鸣、如何避免冷场、如何展现自己的价值

### 6. **关系推进建议**（300-400字）
- **建立初步联系**：具体方法、时机选择、如何避免显得突兀
- **加深了解**：如何逐步深入、如何建立信任、如何展现自己的优势
- **表达好感**：最佳时机、表达方式、如何判断对方是否也有好感、如何避免被拒绝
- **每个阶段都要有具体策略**：例如"在XX情况下，你可以..."

### 7. **收入分析和消费能力**（300-400字）
- **年收入区间预估**（必须给出具体数字）：
  - 从朋友圈内容推断年收入水平，必须给出明确的数字区间（例如：10-15万、20-30万、50-80万等）
  - 分析依据：消费的品牌档次、旅行频率和目的地、居住环境、出行方式、娱乐消费、购物习惯等
  - 必须提供具体证据：例如"从她分享的XX品牌（价格区间XX）可以看出..."、"她每年旅行X次，目的地为XX，预估年收入在XX-XX万"
  
- **月消费水平预估**（必须给出具体数字）：
  - 根据朋友圈内容，预估月消费金额区间（例如：5000-8000元、1-1.5万、2-3万等）
  - 分析消费结构：餐饮消费、购物消费、娱乐消费、旅行消费、其他消费
  - 必须提供具体证据：例如"从她分享的XX可以看出月消费在XX-XX元"
  
- **消费能力分析**：
  - 消费层次：高端消费（月消费2万+）、中高端消费（月消费1-2万）、中等消费（月消费5000-1万）、中低消费（月消费3000-5000元）
  - 消费习惯：是否经常消费高端品牌、是否追求性价比、是否愿意为体验付费
  - 从生活方式判断：居住环境、出行方式、娱乐方式、购物习惯
  - 从社交圈层判断：朋友圈互动的人群、参加的活动类型
  
- **消费心理分析**：分析消费动机、是否理性消费、是否追求品质、是否在意性价比
  
- **消费建议**（必须具体）：
  - 基于预估的消费水平，建议合适的约会场所价格区间（例如：人均200-300元、500-800元等）
  - 建议合适的礼物价格区间（例如：500-1000元、1000-2000元等）
  - 建议日常消费水平（例如：一起吃饭人均XX元、看电影XX元等）
  - 必须提供具体数字建议，不要只说"适中"、"合理"等模糊词汇

### 8. **避雷指南**（200-300字）
- 不仅要列出避免的话题，还要说明：为什么这些话题不合适、如果误触了如何挽回
- 分析对方的敏感点：可能不喜欢什么、可能反感什么行为
- 提供替代方案：如果某个话题不合适，应该聊什么

### 9. **匹配度评分和成功率**
- **匹配度评分**：要综合考虑性格、价值观、生活方式、沟通风格等多个维度，给出0-100分的详细评分
- **脱单成功率**：要分析成功概率，并说明：为什么是这个概率、哪些因素有利于成功、哪些因素可能阻碍、如何提高成功率

## 输出格式要求

请以JSON格式输出，包含以下字段：
{
  "match_score": 85,
  "success_rate": 75,
  "personality": "详细深入的性格分析，200-300字，必须包含具体证据和深层洞察",
  "interests": "深入分析兴趣爱好，150-200字，说明爱好背后的心理需求和如何利用",
  "values": "深入分析价值观，200-300字，必须结合具体内容说明",
  "emotion": "深入分析情感状态，200-300字，包含情感需求和成熟度分析",
  "income_analysis": "深入分析收入和消费能力，300-400字，必须包含：年收入区间预估（具体数字，如10-15万）、月消费水平预估（具体数字，如5000-8000元）、消费能力分析、消费心理、以及基于数字的消费建议（约会场所价格区间、礼物价格区间等）",
  "communication": {
    "topics": ["话题1（说明为什么合适）", "话题2（说明如何引入）", ...],
    "opening_lines": ["开场白1（适用场景：XX）", "开场白2（适用场景：XX）", ...],
    "tips": "详细的聊天技巧，300-400字，包含具体方法和示例"
  },
  "relationship": "详细的关系推进建议，300-400字，分阶段说明具体策略",
  "warnings": "详细的避雷指南，200-300字，说明原因和替代方案",
  "summary": "一句话总结，突出最关键的洞察"
}

## 重要提示

1. **必须深入分析**：不要只停留在表面，要挖掘深层心理和动机
2. **必须提供证据**：每个分析点都要有具体的内容作为支撑
3. **必须具体可操作**：建议要具体到可以立即执行的程度
4. **必须全面细致**：每个字段都要充分展开，不要简单敷衍
5. **只输出JSON**：不要输出Markdown、不要用```包裹、不要在JSON前后加任何解释文字
"""
        
        if supplementary_info:
            info_text = "\n补充信息：\n"
            if supplementary_info.get('gender'):
                info_text += f"- 性别：{supplementary_info['gender']}\n"
            if supplementary_info.get('age'):
                info_text += f"- 年龄：{supplementary_info['age']}\n"
            if supplementary_info.get('occupation'):
                info_text += f"- 职业：{supplementary_info['occupation']}\n"
            if supplementary_info.get('relationship'):
                info_text += f"- 关系：{supplementary_info['relationship']}\n"
            base_prompt += info_text
        
        return base_prompt
    
    def _parse_analysis_result(self, text: str) -> Dict[str, Any]:
        """解析分析结果文本"""
        import json
        import re
        
        # 方法1：尝试直接解析整个文本为JSON
        try:
            parsed = json.loads(text.strip())
            if isinstance(parsed, dict):
                print("[DEBUG] 成功：直接解析为JSON")
                print(f"[DEBUG] 解析后的字段: {list(parsed.keys())}")
                # 确保所有字段都是正确的类型
                normalized = self._normalize_analysis_result(parsed)
                print(f"[DEBUG] 规范化后的字段: {list(normalized.keys())}")
                return normalized
        except Exception as e:
            print(f"[DEBUG] 直接解析失败: {e}")
        
        # 方法2：尝试提取JSON（去掉可能的markdown代码块标记）
        # 去掉 ```json 和 ``` 标记
        cleaned_text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'```\s*', '', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        # 尝试提取第一个完整的JSON对象（支持嵌套）
        # 使用更强大的正则表达式来匹配嵌套的JSON对象
        depth = 0
        start_idx = -1
        for i, char in enumerate(cleaned_text):
            if char == '{':
                if depth == 0:
                    start_idx = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start_idx >= 0:
                    json_str = cleaned_text[start_idx:i+1]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict):
                            print("[DEBUG] 成功：从文本中提取JSON")
                            print(f"[DEBUG] 提取后的字段: {list(parsed.keys())}")
                            normalized = self._normalize_analysis_result(parsed)
                            print(f"[DEBUG] 规范化后的字段: {list(normalized.keys())}")
                            return normalized
                    except Exception as e:
                        print(f"[DEBUG] JSON提取失败: {e}")
                    start_idx = -1
        
        # 方法3：如果无法解析JSON，尝试从文本中提取关键信息
        print("[DEBUG] 警告：无法解析JSON，使用文本提取模式")
        
        # 尝试提取数字（匹配度、成功率）
        match_score = 0
        success_rate = 0
        score_match = re.search(r'匹配度[：:]\s*(\d+)', text)
        if score_match:
            match_score = int(score_match.group(1))
        rate_match = re.search(r'脱单成功率[：:]\s*(\d+)', text)
        if rate_match:
            success_rate = int(rate_match.group(1))
        
        # 如果解析失败，至少把原始文本放到 personality 字段，让前端能看到内容
        return {
            "raw_text": text,
            "summary": text[:200] + "..." if len(text) > 200 else text,
            "match_score": match_score,
            "success_rate": success_rate,
            "personality": text[:1000] if len(text) > 1000 else text,  # 至少显示前1000字符
            "interests": "",
            "values": "",
            "emotion": "",
            "income_analysis": "",
            "communication": {
                "topics": [],
                "opening_lines": [],
                "tips": ""
            },
            "relationship": "",
            "warnings": ""
        }
    
    def _normalize_analysis_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """规范化分析结果，确保所有字段都是正确的类型"""
        result = {
            "match_score": int(data.get("match_score", 0)) if isinstance(data.get("match_score"), (int, float, str)) else 0,
            "success_rate": int(data.get("success_rate", 0)) if isinstance(data.get("success_rate"), (int, float, str)) else 0,
            "personality": str(data.get("personality", "")) if data.get("personality") else "",
            "interests": str(data.get("interests", "")) if data.get("interests") else "",
            "values": str(data.get("values", "")) if data.get("values") else "",
            "emotion": str(data.get("emotion", "")) if data.get("emotion") else "",
            "income_analysis": str(data.get("income_analysis", "")) if data.get("income_analysis") else "",
            "communication": data.get("communication", {}),
            "relationship": str(data.get("relationship", "")) if data.get("relationship") else "",
            "warnings": str(data.get("warnings", "")) if data.get("warnings") else "",
            "summary": str(data.get("summary", "")) if data.get("summary") else ""
        }
        
        # 确保 communication 是字典格式
        if not isinstance(result["communication"], dict):
            result["communication"] = {
                "topics": [],
                "opening_lines": [],
                "tips": ""
            }
        else:
            # 确保 communication 的字段都是正确的类型
            comm = result["communication"]
            if "topics" not in comm or not isinstance(comm["topics"], list):
                comm["topics"] = []
            if "opening_lines" not in comm or not isinstance(comm["opening_lines"], list):
                comm["opening_lines"] = []
            if "tips" not in comm:
                comm["tips"] = str(comm.get("tips", "")) if comm.get("tips") else ""
        
        print(f"[DEBUG] 规范化后的结果:")
        print(f"  - match_score: {result['match_score']}")
        print(f"  - success_rate: {result['success_rate']}")
        print(f"  - personality长度: {len(result['personality'])}")
        print(f"  - interests长度: {len(result['interests'])}")
        print(f"  - values长度: {len(result['values'])}")
        print(f"  - emotion长度: {len(result['emotion'])}")
        print(f"  - income_analysis长度: {len(result['income_analysis'])}")
        print(f"  - relationship长度: {len(result['relationship'])}")
        print(f"  - warnings长度: {len(result['warnings'])}")
        print(f"  - communication: {result['communication']}")
        return result
    
    def chat(
        self,
        analysis_id: int,
        question: str,
        context: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        多轮对话
        
        Args:
            analysis_id: 分析记录ID
            question: 用户问题
            context: 上下文（之前的分析结果）
        
        Returns:
            AI回答
        """
        prompt = f"""基于之前的分析结果，回答用户的问题。

之前的分析结果：
{context or '无'}

用户问题：{question}

请给出简短有效的建议。"""
        
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt}
                    ]
                }
            ],
            "max_output_tokens": 2000,
            "temperature": 0.8,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_url}/responses",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                answer_text = self._extract_responses_output_text(result)
                usage = result.get("usage") or {}
                return answer_text, usage
        except Exception as e:
            raise Exception(f"对话失败: {str(e)}")

    def _extract_responses_output_text(self, resp_json: Dict[str, Any]) -> str:
        """
        从 responses API 返回中提取输出文本
        按照用户的curl示例，可能返回格式：
        - output_text 字段
        - output -> content[] -> {type:"output_text", text:"..."}
        """
        # 有些实现可能直接给 output_text
        if isinstance(resp_json.get("output_text"), str) and resp_json.get("output_text"):
            return resp_json["output_text"]

        # 标准 responses：output -> content[] -> {type:"output_text", text:"..."}
        output = resp_json.get("output") or []
        texts: List[str] = []
        if isinstance(output, list):
            for item in output:
                content = (item or {}).get("content") or []
                if not isinstance(content, list):
                    continue
                for c in content:
                    ctype = (c or {}).get("type")
                    if ctype in ("output_text", "text", "output_text_delta"):
                        t = (c or {}).get("text") or ""
                        if t:
                            texts.append(t)
        if texts:
            return "".join(texts).strip()

        # 兜底：返回整个 JSON 的字符串（便于排错）
        try:
            import json
            return json.dumps(resp_json, ensure_ascii=False)[:4000]
        except Exception:
            return str(resp_json)[:4000]
    
    def _extract_chat_output_text(self, resp_json: Dict[str, Any]) -> str:
        """
        兼容方法：如果以后需要支持 chat/completions API，可以保留此方法
        目前统一使用 _extract_responses_output_text
        """
        return self._extract_responses_output_text(resp_json)
    
    def _extract_output_text(self, resp_json: Dict[str, Any]) -> str:
        """
        兼容方法别名
        """
        return self._extract_responses_output_text(resp_json)
