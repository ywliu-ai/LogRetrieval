from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
from datetime import timedelta, datetime
import os
from elasticsearch import Elasticsearch
import fnmatch

elasticsearch_usr = os.environ.get("ELK_USR", "")
elasticsearch_pwd = os.environ.get("ELK_PWD", "")
url_247 = os.environ.get("URL247", "")
url_191 = os.environ.get("URL191", "")

ES_INDEX_ROUTER = {
    "arp_vpn*": url_247,
    "cas_apache_abnormal*": url_247,
    "cas_nginx_abnormal*": url_247,
    "email_access*": url_247,
    "email_user_action_2026*": url_247,
    "email_firewall*": url_247,
    "kjyp_xserver_acc*": url_247,
    "pass_access*": url_247,
    "pass_user_action_2026*": url_247,
    "pass_security_bastion*": url_247,
    "vpn_abnormal_whole*": url_247,
    "cnic_system_access": url_191,
    "cnic_system_assets": url_191,
    "sangfor_edr*": url_191,
    "znt_comprehensive_result_v4": url_191,
    "znt_comprehensive_result_zuduan": url_191,
}

FIELD_MAPPINGS = {
    "arp_vpn*": {
        "ip_field": "ip",
        "timestamp_field": "createDate"
    },
    #"arp_firewall*"
    "cas_apache_abnormal*": {
        "ip_field": "iP",  # 支持多个可能的IP字段
        "timestamp_field": "create_date"
    },
    "cas_nginx_abnormal*": {
        "ip_field": "iP",
        "timestamp_field": "create_date"
    },
    "email_access*": {
        "ip_field": "IP",
        "timestamp_field": "create_date"
    },
    "email_user_action_2026*": {
        "ip_field": "IP",
        "timestamp_field": "create_date"
    },
    "email_firewall*": {
        "ip_field": ["srcIP", "dstIP"],
        "timestamp_field": "create_date"
    },
    "kjyp_xserver_acc*": {
        "ip_field": "ip",
        "timestamp_field": "datetime"
    },
    "pass_access*": {
        "ip_field": "clientIp",
        "timestamp_field": "create_date"
    },
    "pass_user_action_2026*": {
        "ip_field": "IP",
        "timestamp_field": "create_date"
    },
    "pass_security_bastion*": {
        "ip_field": "devIp",
        "timestamp_field": "operationTime"
    },
    "vpn_abnormal_whole*": {
        "ip_field": "srcIp",
        "timestamp_field": "create_date"
    },
    #"security_system_nginx*"
    #"cnic_system_access"
    #"cnic_system_assets"
    "sangfor_edr*": {
        "ip_field": "iplist",
        "timestamp_field": "@timestamp"
    },
    "znt_comprehensive_result_v4": {
        "ip_field": ["originalInfo.src_ip", "originalInfo.dst_ip"],
        "timestamp_field": "originalInfo.timestrings"
    },
    "znt_comprehensive_result_zuduan": {
        "ip_field": ["originalInfo.src_ip", "originalInfo.dst_ip"],
        "timestamp_field": "originalInfo.timestring"
    },
}

class LogRetrievalToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    Ip: str = Field(..., description="目标IP地址")
    Index: str = Field(..., description="ELK索引名称")
    Url: str = Field(..., description="ELK集群地址")
    Account: str = Field(..., description="用户账号")
    StartTime: Optional[str] = Field(None, description="查询开始时间，格式为YYYY-MM-DD HH:MM:SS，默认为过去24小时")
    EndTime: Optional[str] = Field(None, description="查询结束时间，格式为YYYY-MM-DD HH:MM:SS，默认为当前时间")
    
    
class LogRetrievalBasedOnIp(BaseTool):
    name: str = "LogRetrievalBasedOnIp"
    description: str = """灵活的日志、告警、安全事件检索工具：可基于输入的IP查询并返回匹配的内容；即使未提供IP参数，也能返回最近检索到的内容，确保在各种场景下都能使用\n\n    When to use:\n    - 当需要根据特定源IP和目标IP检索信息时\n    - 当需要查看最近的数据活动概况时\n    - 当需要调查特定IP地址相关的日志事件时\n    - 当需要分析IP间的关联数据行为时\n    - 当需要通用数据信息检索服务时（无需指定具体IP）"""
    args_schema: Type[BaseModel] = LogRetrievalToolInput

    def _get_es_url(self, index_name: str):
        for pattern, url in ES_INDEX_ROUTER.items():
            if fnmatch.fnmatch(index_name, pattern):
                return url
        raise ValueError(f"No ES url found for index: {index_name}")

    def _get_field_mapping(self, index_name: str):
        """获取索引的字段映射配置"""
        # 按优先级匹配映射
        for pattern, fields in FIELD_MAPPINGS.items():
            if fnmatch.fnmatch(index_name, pattern):
                return fields

            # 默认（防止报错）
        return {
            "ip_field": "IP",
            "timestamp_field": "create_date"
        }

    def _format_to_markdown(self, data_list):
        """将字典列表格式化为Markdown表格"""

        if not data_list:
            return ""

        # 收集所有字典中出现过的键
        all_keys = []
        seen = set()

        for item in data_list:
            for key in item.keys():
                if key not in seen:
                    seen.add(key)
                    all_keys.append(key)

        headers = all_keys
        markdown = "| " + " | ".join(headers) + " |\n"
        markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        for item in data_list:
            row = []
            for header in headers:
                # 使用get方法，如果键不存在则返回空字符串
                value = item.get(header, "")
                row.append(str(value))
            markdown += "| " + " | ".join(row) + " |\n"

        return markdown

    def _run(self, Ip: str, Index: str, Url: str, Account: str, StartTime: Optional[str] = None, EndTime: Optional[str] = None) -> str:
        #url = "http://159.226.16.247:9200/"
        #print("Using Elasticsearch username:", elasticsearch_usr)
        #print("Using Elasticsearch password:", elasticsearch_pwd)
        # 注意：这里需要通过其他方式获取默认时间，因为无法直接在类上调用实例方法
        if StartTime is None:
            now = datetime.now()
            start_time = now - timedelta(hours=1)
            StartTime = int(start_time.timestamp())  # 转为整数时间戳（秒）
        else:
            StartTime = int(datetime.strptime(StartTime, "%Y-%m-%d %H:%M:%S").timestamp())

        if EndTime is None:
            EndTime = int(datetime.now().timestamp())
        else:
            EndTime = int(datetime.strptime(EndTime, "%Y-%m-%d %H:%M:%S").timestamp())

        print("Using start time:", StartTime, "Using end time:", EndTime)
        es_url = self._get_es_url(Index)
        es = Elasticsearch(
            [es_url],
            basic_auth=(elasticsearch_usr, elasticsearch_pwd)
        )

        # 检测字段
        field_mapping = self._get_field_mapping(Index)
        ip_field = field_mapping["ip_field"]
        time_field = field_mapping["timestamp_field"]

        if not ip_field:
            return f"错误: 在索引 {Index} 中未找到IP字段。"

        if not time_field:
            return f"错误: 在索引 {Index} 中未找到时间字段。"

        print(f"[INFO] Using ip_field={ip_field}, time_field={time_field}")

        # 构建查询
        # 处理IP字段可能是列表的情况
        if isinstance(ip_field, list):
            # 如果有多个可能的IP字段，使用should查询
            ip_conditions = []
            for field in ip_field:
                ip_conditions.append({"term": {field: Ip}})
            ip_query = {"bool": {"should": ip_conditions, "minimum_should_match": 1}}
        else:
            # 单个IP字段
            ip_query = {"term": {ip_field: Ip}}

        # 处理时间范围查询
        time_query = {
            "range": {
                time_field: {
                    "gte": str(StartTime),
                    "lte": str(EndTime)
                }
            }
        }

        query = {
            "query": {
                "bool": {
                    "must": [ip_query, time_query]
                }
            },
            "from": 0
        }

        print(f"使用的查询条件: {query}")

        try:
            response = es.search(index=Index, body=query, size=5000, scroll='2m')

            # 提取命中的数据
            hits = response['hits']['hits']
            if hits:
                # 提取源数据并转换为列表格式
                data_list = [hit['_source'] for hit in hits]
                # 将结果格式化为markdown表格
                markdown_result = self._format_to_markdown(data_list)
                return f"找到 {len(hits)} 条记录:\n\n" + markdown_result
            else:
                return f"在索引 {Index} 中未找到匹配 IP {Ip} 的日志数据"

        except Exception as e:
            return f"查询失败: {str(e)}"


def main():
    # 示例：使用新工具类
    tool = LogRetrievalBasedOnIp()
    # 如果提供时间参数，则使用提供的参数；否则将使用默认的过去24小时
    result = tool._run(Ip="159.226.184.138", Index="sangfor_edr*")
    print(result)
if __name__ == "__main__":
    main()