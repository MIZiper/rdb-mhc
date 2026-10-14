export interface Coefficients {
    [name: string]: number;
}

export interface FormulaDef {
    name: string;
    expression: string;
    coefficients: Coefficients;
    xmin: number;
    xmax: number;
    note?: string;
}

export interface FormulaContent {
    type: "formula";
    formulas: FormulaDef[];
}

export interface Point {
    x: number;
    y: number;
}

type AstNode =
    | { kind: "num"; value: number }
    | { kind: "var"; name: string }
    | { kind: "unary"; op: "-" | "+"; arg: AstNode }
    | { kind: "binary"; op: "+" | "-" | "*" | "/" | "^"; left: AstNode; right: AstNode }
    | { kind: "call"; name: string; args: AstNode[] };

export const CONSTANTS: Record<string, number> = {
    pi: Math.PI,
    e: Math.E,
};

type MathFn = (...args: number[]) => number;

export const FUNCTIONS: Record<string, MathFn> = {
    sin: Math.sin,
    cos: Math.cos,
    tan: Math.tan,
    asin: Math.asin,
    acos: Math.acos,
    atan: Math.atan,
    sinh: Math.sinh,
    cosh: Math.cosh,
    tanh: Math.tanh,
    exp: Math.exp,
    ln: Math.log,
    log: Math.log,
    log10: Math.log10,
    log2: Math.log2,
    sqrt: Math.sqrt,
    cbrt: Math.cbrt,
    abs: Math.abs,
    ceil: Math.ceil,
    floor: Math.floor,
    round: Math.round,
    sign: Math.sign,
    pow: Math.pow,
    min: Math.min,
    max: Math.max,
    atan2: Math.atan2,
    hypot: Math.hypot,
};

interface Token {
    type: "num" | "ident" | "op" | "lparen" | "rparen" | "comma";
    value: string;
    pos: number;
}

function tokenize(input: string): Token[] {
    const tokens: Token[] = [];
    let i = 0;
    while (i < input.length) {
        const ch = input[i];
        if (/\s/.test(ch)) {
            i++;
            continue;
        }
        if (/[0-9.]/.test(ch)) {
            const rest = input.slice(i);
            const m = rest.match(/^(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?/);
            if (!m) throw new Error(`Invalid number at position ${i}`);
            tokens.push({ type: "num", value: m[0], pos: i });
            i += m[0].length;
            continue;
        }
        if (/[A-Za-z_]/.test(ch)) {
            const rest = input.slice(i);
            const m = rest.match(/^[A-Za-z_][A-Za-z0-9_]*/);
            if (!m) throw new Error(`Invalid identifier at position ${i}`);
            tokens.push({ type: "ident", value: m[0], pos: i });
            i += m[0].length;
            continue;
        }
        if ("+-*/^".includes(ch)) {
            tokens.push({ type: "op", value: ch, pos: i });
            i++;
            continue;
        }
        if (ch === "(") {
            tokens.push({ type: "lparen", value: ch, pos: i });
            i++;
            continue;
        }
        if (ch === ")") {
            tokens.push({ type: "rparen", value: ch, pos: i });
            i++;
            continue;
        }
        if (ch === ",") {
            tokens.push({ type: "comma", value: ch, pos: i });
            i++;
            continue;
        }
        throw new Error(`Unexpected character "${ch}" at position ${i}`);
    }
    return tokens;
}

class Parser {
    private tokens: Token[];
    private pos = 0;

    constructor(tokens: Token[]) {
        this.tokens = tokens;
    }

    private peek(): Token | undefined {
        return this.tokens[this.pos];
    }

    private next(): Token {
        const t = this.tokens[this.pos];
        if (!t) throw new Error("Unexpected end of expression");
        this.pos++;
        return t;
    }

    parse(): AstNode {
        if (this.tokens.length === 0) throw new Error("Empty expression");
        const node = this.parseExpr();
        const trailing = this.peek();
        if (trailing) {
            throw new Error(`Unexpected token "${trailing.value}" at position ${trailing.pos}`);
        }
        return node;
    }

    private parseExpr(): AstNode {
        let left = this.parseTerm();
        for (;;) {
            const t = this.peek();
            if (t && t.type === "op" && (t.value === "+" || t.value === "-")) {
                this.next();
                const right = this.parseTerm();
                left = { kind: "binary", op: t.value as "+" | "-", left, right };
            } else {
                break;
            }
        }
        return left;
    }

    private parseTerm(): AstNode {
        let left = this.parseUnary();
        for (;;) {
            const t = this.peek();
            if (t && t.type === "op" && (t.value === "*" || t.value === "/")) {
                this.next();
                const right = this.parseUnary();
                left = { kind: "binary", op: t.value as "*" | "/", left, right };
            } else {
                break;
            }
        }
        return left;
    }

    private parseUnary(): AstNode {
        const t = this.peek();
        if (t && t.type === "op" && (t.value === "-" || t.value === "+")) {
            this.next();
            const arg = this.parseUnary();
            return { kind: "unary", op: t.value as "-" | "+", arg };
        }
        return this.parsePower();
    }

    private parsePower(): AstNode {
        const base = this.parsePrimary();
        const t = this.peek();
        if (t && t.type === "op" && t.value === "^") {
            this.next();
            const exponent = this.parseUnary();
            return { kind: "binary", op: "^", left: base, right: exponent };
        }
        return base;
    }

    private parsePrimary(): AstNode {
        const t = this.next();
        if (t.type === "num") {
            return { kind: "num", value: parseFloat(t.value) };
        }
        if (t.type === "ident") {
            const upper = this.peek();
            if (upper && upper.type === "lparen") {
                this.next();
                const args: AstNode[] = [];
                if (this.peek()?.type !== "rparen") {
                    args.push(this.parseExpr());
                    while (this.peek()?.type === "comma") {
                        this.next();
                        args.push(this.parseExpr());
                    }
                }
                const close = this.next();
                if (close.type !== "rparen") {
                    throw new Error(`Expected ")" at position ${close.pos}`);
                }
                return { kind: "call", name: t.value, args };
            }
            return { kind: "var", name: t.value };
        }
        if (t.type === "lparen") {
            const inner = this.parseExpr();
            const close = this.next();
            if (close.type !== "rparen") {
                throw new Error(`Expected ")" at position ${close.pos}`);
            }
            return inner;
        }
        throw new Error(`Unexpected token "${t.value}" at position ${t.pos}`);
    }
}

export function parseExpression(expression: string): AstNode {
    return new Parser(tokenize(expression)).parse();
}

export function extractVariables(expression: string): string[] {
    const seen = new Set<string>();
    for (const tok of tokenize(expression)) {
        if (tok.type !== "ident") continue;
        if (tok.value in FUNCTIONS) continue;
        if (tok.value in CONSTANTS) continue;
        seen.add(tok.value);
    }
    return [...seen].sort();
}

function evaluateNode(node: AstNode, scope: Record<string, number>): number {
    switch (node.kind) {
        case "num":
            return node.value;
        case "var": {
            if (node.name in scope) return scope[node.name];
            if (node.name in CONSTANTS) return CONSTANTS[node.name];
            throw new Error(`Unknown variable "${node.name}"`);
        }
        case "unary": {
            const v = evaluateNode(node.arg, scope);
            return node.op === "-" ? -v : v;
        }
        case "binary": {
            const a = evaluateNode(node.left, scope);
            const b = evaluateNode(node.right, scope);
            switch (node.op) {
                case "+":
                    return a + b;
                case "-":
                    return a - b;
                case "*":
                    return a * b;
                case "/":
                    return a / b;
                case "^":
                    return Math.pow(a, b);
            }
        }
        case "call": {
            const fn = FUNCTIONS[node.name];
            if (!fn) throw new Error(`Unknown function "${node.name}"`);
            return fn(...node.args.map((arg) => evaluateNode(arg, scope)));
        }
    }
}

export function evaluateExpression(
    expression: string,
    coefficients: Coefficients,
    x: number,
): number {
    const ast = parseExpression(expression);
    return evaluateNode(ast, { ...coefficients, x });
}

export function normalizeDomain(formula: Pick<FormulaDef, "xmin" | "xmax">): [number, number] {
    let min = Number.isFinite(formula.xmin) ? formula.xmin : -10;
    let max = Number.isFinite(formula.xmax) ? formula.xmax : 10;
    if (min === max) {
        min -= 1;
        max += 1;
    }
    if (min > max) {
        [min, max] = [max, min];
    }
    return [min, max];
}

export function evaluateFormulaAt(formula: FormulaDef, x: number): number | null {
    try {
        const y = evaluateExpression(formula.expression, formula.coefficients ?? {}, x);
        return Number.isFinite(y) ? y : null;
    } catch {
        return null;
    }
}

export function sampleCurve(formula: FormulaDef, sampleCount = 200): Point[] {
    const [min, max] = normalizeDomain(formula);
    const n = Math.max(2, Math.min(2000, Math.floor(sampleCount)));
    const points: Point[] = [];
    for (let i = 0; i < n; i++) {
        const x = min + ((max - min) * i) / (n - 1);
        const y = evaluateFormulaAt(formula, x);
        if (y !== null) points.push({ x, y });
    }
    return points;
}

export function parseFormulaContent(content: unknown): FormulaContent | null {
    let value = content;
    if (typeof value === "string") {
        try {
            value = JSON.parse(value);
        } catch {
            return null;
        }
    }
    if (!value || typeof value !== "object") return null;
    const formulas = (value as { formulas?: unknown }).formulas;
    if (!Array.isArray(formulas)) return null;
    return {
        type: "formula",
        formulas: formulas.map((f, i) => {
            const raw = (f ?? {}) as Partial<FormulaDef>;
            const coefficients = (raw.coefficients && typeof raw.coefficients === "object")
                ? raw.coefficients
                : {};
            return {
                name: typeof raw.name === "string" && raw.name ? raw.name : `f${i + 1}`,
                expression: typeof raw.expression === "string" ? raw.expression : "",
                coefficients,
                xmin: typeof raw.xmin === "number" ? raw.xmin : -10,
                xmax: typeof raw.xmax === "number" ? raw.xmax : 10,
                note: typeof raw.note === "string" ? raw.note : "",
            };
        }),
    };
}
