function index_temp = sample_dense(parent_lat,...
                               parent_long,...
                               LATITUDE,...
                               LONGITUDE,...
                               depth,...
                               total_rem,...
                               index_total,...
                               threshold)
                           
                           
if total_rem ~= length(index_total)
    error('Shit!');
end

cands = [];
for i = 1 : total_rem
    if norm([LONGITUDE(index_total(i)) - parent_long,...
             LATITUDE(index_total(i)) - parent_lat]) <= threshold
        cands = [cands index_total(i)]; %#ok<AGROW>
    end
end



if length(cands) >= depth
    index = randperm(length(cands), depth);
    index_temp = cands(index);
else
    error('Not Enough Airports!');
end

