public class ArrayProcessor {
    public int getElement(int[] arr, int index) {
        return arr[index];  // BUG: No bounds checking
    }
}