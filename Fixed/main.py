from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Fixed Size Queue API")

# GAS(Google Apps Script) 웹앱과의 CORS 통신 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FixedQueue:
    """고정 크기 원형/선형 개념을 적용한 큐 클래스"""
    def __init__(self, capacity: int = 20):
        self.capacity = capacity
        self.queue = [None] * capacity
        self.front = 0
        self.rear = 0
        self.count = 0

    def is_empty(self) -> bool:
        """큐가 비어있는지 검사 (기능 4)"""
        return self.count == 0

    def is_full(self) -> bool:
        """큐가 가득 찼는지 검사 (기능 4)"""
        return self.count == self.capacity

    def push(self, value: int):
        """큐에 데이터 삽입 (기능 2)"""
        if self.is_full():
            raise HTTPException(status_code=400, detail="Queue Overflow: 큐가 가득 찼습니다.")
        self.queue[self.rear] = value
        self.rear = (self.rear + 1) % self.capacity
        self.count += 1

    def pop(self):
        """큐에서 데이터 추출 (기능 2)"""
        if self.is_empty():
            raise HTTPException(status_code=400, detail="Queue Underflow: 큐가 비어있습니다.")
        val = self.queue[self.front]
        self.queue[self.front] = None
        self.front = (self.front + 1) % self.capacity
        self.count -= 1
        return val

    def peek(self):
        """전면(Front) 데이터 확인 (기능 5)"""
        if self.is_empty():
            return None
        return self.queue[self.front]

    def clear(self):
        """큐 전체 데이터 삭제 및 초기화 (기능 1, 6)"""
        self.queue = [None] * self.capacity
        self.front = 0
        self.rear = 0
        self.count = 0

    def find_index(self, value: int) -> int:
        """Front 기준으로 해당 값의 논리적 index 검색 (기능 7)"""
        for i in range(self.count):
            idx = (self.front + i) % self.capacity
            if self.queue[idx] == value:
                return i  # Front로부터 몇 번째 위치인지 반환 (0-based)
        return -1

    def count_value(self, value: int) -> int:
        """특정 값의 개수 반환 (기능 8)"""
        cnt = 0
        for i in range(self.count):
            idx = (self.front + i) % self.capacity
            if self.queue[idx] == value:
                cnt += 1
        return cnt

    def contains(self, value: int) -> bool:
        """값의 존재 여부 검사 (기능 9)"""
        return self.find_index(value) != -1

    def get_all_data(self) -> List[int]:
        """Front부터 Rear까지 전체 데이터 리스트 출력 (기능 10)"""
        result = []
        for i in range(self.count):
            idx = (self.front + i) % self.capacity
            result.append(self.queue[idx])
        return result

# 싱글톤 형태의 전역 큐 인스턴스 (기본 크기 20)
global_queue = FixedQueue(capacity=20)


# --- API Request/Response 스키마 ---
class InitRequest(BaseModel):
    capacity: int = 20

class PushBatchRequest(BaseModel):
    items: List[int]

class SearchRequest(BaseModel):
    value: int


# --- API Endpoints ---

@app.post("/init")
def init_queue(req: InitRequest):
    """1) 초기화 (기능 1)"""
    global global_queue
    global_queue = FixedQueue(capacity=req.capacity)
    return {"message": f"큐가 크기 {req.capacity}(으)로 초기화되었습니다.", "capacity": req.capacity}

@app.post("/push_batch")
def push_batch(req: PushBatchRequest):
    """2) 배열 PUSH (기능 2)"""
    pushed_items = []
    for item in req.items:
        if global_queue.is_full():
            break
        global_queue.push(item)
        pushed_items.append(item)
    return {
        "message": f"{len(pushed_items)}개 항목이 PUSH 되었습니다.",
        "pushed_items": pushed_items,
        "current_data": global_queue.get_all_data()
    }

@app.get("/status")
def get_status():
    """3) 현재 데이터 개수, 4) 상태 검사(full, empty) (기능 3, 4)"""
    return {
        "capacity": global_queue.capacity,
        "count": global_queue.count,  # 기능 3: 현재 데이터 개수 반환
        "is_empty": global_queue.is_empty(),  # 기능 4: empty 여부
        "is_full": global_queue.is_full()     # 기능 4: full 여부
    }

@app.get("/peek")
def peek_front():
    """5) 전면(Front) 데이터 확인 (기능 5)"""
    val = global_queue.peek()
    return {"front_data": val, "is_empty": global_queue.is_empty()}

@app.post("/clear")
def clear_queue():
    """6) 큐 전체 데이터 삭제 (기능 6)"""
    global_queue.clear()
    return {"message": "큐의 모든 데이터가 삭제되었습니다.", "current_data": []}

@app.post("/search_value")
def search_value(req: SearchRequest):
    """7) index 검색, 8) 값의 개수, 9) 존재 여부 검사 (기능 7, 8, 9)"""
    index = global_queue.find_index(req.value)      # 기능 7
    count = global_queue.count_value(req.value)     # 기능 8
    exists = global_queue.contains(req.value)        # 기능 9
    return {
        "target_value": req.value,
        "index_from_front": index,
        "count": count,
        "exists": exists
    }

@app.get("/print_all")
def print_all():
    """10) Front부터 Rear까지 출력 (기능 10) 및 시각화용 단순 삽입 정렬 수행 단계 반환"""
    data = global_queue.get_all_data()
    
    # 시각화용 단순 삽입 정렬(Insertion Sort) 단계별 과정 기록
    sort_steps = []
    arr = list(data)
    
    # 초기 상태 기록
    sort_steps.append({
        "step": 0,
        "description": "정렬 시작 전 큐 데이터 상태",
        "array": list(arr),
        "highlight_idx": -1,
        "compare_idx": -1
    })
    
    # 단순 삽입 정렬 수행
    n = len(arr)
    step_cnt = 1
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        
        # 비교 단계 기록
        sort_steps.append({
            "step": step_cnt,
            "description": f"단계 {step_cnt}: Key 값 {key} (인덱스 {i}) 선택 후 이전 요소들과 비교",
            "array": list(arr),
            "highlight_idx": i,
            "compare_idx": j
        })
        step_cnt += 1
        
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            sort_steps.append({
                "step": step_cnt,
                "description": f"단계 {step_cnt}: {arr[j]} > {key} 이므로 오른쪽으로 이치 이동",
                "array": list(arr),
                "highlight_idx": j + 1,
                "compare_idx": j
            })
            step_cnt += 1
            j -= 1
            
        arr[j + 1] = key
        sort_steps.append({
            "step": step_cnt,
            "description": f"단계 {step_cnt}: 위치 {j + 1} 에 Key 값 {key} 삽입 완료",
            "array": list(arr),
            "highlight_idx": j + 1,
            "compare_idx": -1
        })
        step_cnt += 1

    return {
        "raw_queue_data": data,            # Front부터 Rear까지 큐 원래 데이터
        "insertion_sort_steps": sort_steps # 단순 삽입 정렬 단계별 데이터 (클라이언트 시각화용)
    }
