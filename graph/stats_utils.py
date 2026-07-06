"""Utility functions cho observability / node stats."""


def count_rejects(gate_history: list[dict], gate_name: str) -> int:
    """Đếm số lần bị reject ở một gate cụ thể.
    
    Args:
        gate_history: Danh sách lịch sử gate từ state
        gate_name: Tên gate cần đếm (e.g. 'gate_prd')
        
    Returns:
        Số lần gate đó bị decision='reject'
    """
    return sum(1 for h in gate_history if h.get("gate") == gate_name and h.get("decision") == "reject")
