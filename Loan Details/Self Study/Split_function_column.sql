Select * from (
    Select value, RowN = Row_Number() over (order by value) from STRING_SPLIT('a,b,c', ',')
    ) a
    pivot (max(value) for RowN in ([1],[2],[3],[4],[5])) p;
create or replace table Tempb

splite big file into multiple files
https://www.youtube.com/watch?v=WgTFs0eNRpA