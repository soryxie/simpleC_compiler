int binarySearch(int arr[10], int len, int val) {
    /**
     * given the array and the value, returns
     * true or false
     */
    int l, r;
    for (l = 0, r = len; l < r; ) {
        int mid = l + (r - l) / 2;
        if (arr[mid] < val) {
            l = mid + 1;
        } else {
            r = mid;
        }
    }
    return (arr[l] == val);
}

int main() {
    int n = 10;
    int arr[10];
    for (int i = 0; i < n; ++i) {
        arr[i] = i;
    }

    int query = 8;
    int result = binarySearch(arr, 10, query);
    int ans;
    if (result == 0) {
        ans = 0;
    } else {
        ans = 1;
    }

    return ans;
}