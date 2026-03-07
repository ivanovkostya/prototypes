from fastapi import FastAPI, HTTPException, Form

app = FastAPI()

current_expr = ""

# 1. Простые арифметические операции
@app.post("/add")
def add(a: float = Form(...), b: float = Form(...)):
    return {"result": a + b}

@app.post("/subtract")
def subtract(a: float = Form(...), b: float = Form(...)):
    return {"result": a - b}

@app.post("/multiply")
def multiply(a: float = Form(...), b: float = Form(...)):
    return {"result": a * b}

@app.post("/divide")
def divide(a: float = Form(...), b: float = Form(...)):
    if b == 0:
        raise HTTPException(400, "Деление на ноль")
    return {"result": a / b}

# 2. Метод для бинарных операций (a, op, b)
@app.post("/operation")
def operation(a: float = Form(...), b: float = Form(...), op: str = Form(...)):
    if op == "+":
        res = a + b
    elif op == "-":
        res = a - b
    elif op == "*":
        res = a * b
    elif op == "/":
        if b == 0:
            raise HTTPException(400, "Деление на ноль")
        res = a / b
    else:
        raise HTTPException(400, "Неверная операция")
    return {"result": res}

# 3. Метод создания сложного выражения
@app.post("/expression")
def create_expression(expr: str = Form(...)):
    global current_expr
    current_expr = expr
    return {"message": "Выражение сохранено"}

# 4. Метод просмотра текущего выражения
@app.get("/current-expression")
def get_current():
    return {"expression": current_expr}

@app.get("/execute")
def execute():
    if not current_expr:
        raise HTTPException(400, "Нет выражения для вычисления")
    try:
        result = eval(current_expr)
        return {"result": result}
    except:
        raise HTTPException(400, "Ошибка вычисления")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)