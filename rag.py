from typing import List
import requests
from langchain.embeddings.base import Embeddings
from langchain_chroma import Chroma
import uuid
import os

from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("EMBEDDING_OPENAI_API_KEY", "")
model_name = os.environ.get("EMBEDDING_OPENAI_MODEL_NAME", "")
endpoint = os.environ.get("EMBEDDING_OPENAI_ENDPOINT", "")

class EmbeddingService:
    """嵌入向量服务类"""
    
    def __init__(self):
        self.api_url = endpoint
        self.api_token = api_key  # API密钥应该赋值给api_token
        self.model_name = model_name  # 模型名称应该赋值给model_name
    
    def get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model_name,
            "input": text
        }
        response = requests.post(self.api_url, json=data, headers=headers)

        if response.status_code == 200:
            embedding = response.json().get("data", [{}])[0].get("embedding", [])
            return embedding
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return []


class CloudEmbeddings(Embeddings):
    """LangChain兼容的嵌入向量服务"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embedding_service.get_embedding(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embedding_service.get_embedding(text)


class Analyzer:
    """分析器类"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.docs = [
            {"name": "arp_vpn*",
             "description": "arp系统的用户行为日志",
            },
            {"name": "arp_firewall*",
             "description": "arp系统的防火墙日志",
             },
            {"name": "cas_apache_abnormal*",
             "description": "网站群apache服务器异常",
            },
            {"name": "cas_nginx_abnormal*",
             "description": "网站群nginx服务器异常",
             },
            {"name": "email_access*",
             "description": "邮件系统apache服务器的访问日志，存储用户的访问记录",
            },
            {"name": "email_user_action_2026*",
             "description": "邮件系统用户行为日志",
            },
            {"name": "email_firewall*",
             "description": "邮件系统的防火墙日志",
             },
            {"name": "kjyp_xserver_acc*",
             "description": "科技云盘的用户行为日志",
            },
            {"name": "pass_access*",
             "description": "通行证系统apache服务器的访问日志",
             },
            {"name": "pass_user_action_2026*",
             "description": "通行证系统用户行为日志",
            },
            {"name": "pass_security_bastion*",
             "description": "通行证系统堡垒机日志",
             },
            {"name": "vpn_abnormal_whole*",
             "description": "arp系统、网站群、地球大数据系统VPN异常",
            },
            {"name": "security_system_nginx*",
             "description": "科技云盘、攻坚平台的nginx日志",
            },
            {"name": "cnic_system_access",
             "description": "所有系统归属信息",
             },
            {"name": "cnic_system_assets",
             "description": "所有资产归属信息",
             },
            {"name": "sangfor_edr*",
             "description": "终端的EDR日志",
             },
            {"name": "znt_comprehensive_result_v4",
             "description": "经人工研判后的流量告警日志",
             },
            {"name": "znt_comprehensive_result_zuduan",
             "description": "科技云盘、攻坚平台的nginx日志",
             },
        ]
        documents = []
        for doc in self.docs:
            embedding = self.embedding_service.get_embedding(doc['description'])
            documents.append({
                'name': doc['name'],
                'description': doc['description'],
                'embedding': embedding,
            })

        embedding_function = CloudEmbeddings()
        collection_name = f"rag-chroma-{uuid.uuid4()}"
        chroma = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_function
        )

        # 主要使用description作为索引内容，name只作为辅助
        documents_texts = [
            doc["description"]
            for doc in documents
        ]
        metadatas = [
            {
                "name": doc["name"],
                "description": doc["description"]
            }
            for doc in documents
        ]
        chroma.add_texts(texts=documents_texts, metadatas=metadatas)
        self.retriever = chroma.as_retriever()
    
    def analyze(self, question: str, topk: int=3) -> dict:
        """分析问题并返回相应的索引"""
        results = self.retriever.invoke(question)
        try:
            Chroma.delete_collection(collection_name)
        except Exception:
            try:
                chroma.delete_collection()
            except Exception:
                pass

        if results:
            name = []
            results = results[:topk]
            for result in results:
                name.append(result.metadata['name'])
            return {"所需要的日志可能包含在index_name中": name,}
        else:
            return {"index_name":"未找到相关索引"}



def main():
    analyzer = Analyzer()
    question = "我想查询ARP系统的用户行为日志，应该使用哪个索引呢？"
    result = analyzer.analyze(question)
    print(result)

if __name__ == "__main__":
    main()
