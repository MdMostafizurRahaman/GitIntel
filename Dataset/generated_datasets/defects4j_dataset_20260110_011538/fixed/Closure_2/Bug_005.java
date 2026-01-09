public class ArrayProcessor {
    public int getElement(int[] arr, int index) {
        if (arr == null || index < 0 || index >= arr.length) {
            throw new IndexOutOfBoundsException("Invalid array access");
        }
        return arr[index];
    }
}