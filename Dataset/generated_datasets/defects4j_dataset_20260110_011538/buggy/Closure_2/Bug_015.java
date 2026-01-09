public class Calculator {
    public int divide(int a, int b) {
        return a / b;  // BUG: No division by zero check
    }
}