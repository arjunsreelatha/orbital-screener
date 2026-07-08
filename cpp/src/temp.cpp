class Solution {
public:
    vector<vector<int>> filterOccupiedIntervals(vector<vector<int>>& occupiedIntervals, int freeStart, int freeEnd) {
        for(auto& v:occupiedIntervals)
        {
            if(v[0]>freeStart&&v[0]<freeEnd)
            {
                v[0] = freeEnd+1;
            }
            if(v[1]>freeStart&&v[1]<freeEnd)
            {
                v[1] = freeStar-1;
            }
        }
        
    }
};