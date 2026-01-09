public class StringUtils {
    public String process(String input) {
        return input.toUpperCase();  // BUG: Null pointer if input is null
    }
}