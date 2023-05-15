int binarySearch(int arr, int len, int val) {
    /**
     * given the array and the value, returns
     * the index of the val, or -1 if not found
     */
    int l, r;
    for (l = 0, r = len; l < r; ) {
        int mid = l + (r - l) / 2;
        if (arr[mid] == val) {
            l = r = mid;
        } else if (arr[mid] < val) {
            l = mid + 1;
        } else {
            r = mid;
        }
    }
    // assert l == r;
    if (arr[l] == val) {
        return l;
    } else {
        return -1;
    }
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
    if (result == -1) {
        ans = 0;
    } else {
        ans = 1;
    }

    return ans;
}