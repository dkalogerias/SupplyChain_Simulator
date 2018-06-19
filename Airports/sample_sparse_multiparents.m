function index_temp = sample_sparse_multiparents(parent_lat,...
                               parent_long,...
                               list_parpar_lat,...
                               list_parpar_long,...
                               LATITUDE,...
                               LONGITUDE,...
                               depth,...
                               total_rem,...
                               index_total,...
                               threshold_down,...
                               threshold_up,...
                               th_phi)
if total_rem ~= length(index_total)
    error('Shit!');
end
cands = [];
num_parents = length(list_parpar_lat);
if length(list_parpar_long) ~= num_parents
    error('Shit!');
end
for i = 1 : total_rem
    x = [parent_long - LONGITUDE(index_total(i)), parent_lat - LATITUDE(index_total(i))];
    list_cosphi = zeros(1, num_parents);
    for j = 1:num_parents
        y = -[list_parpar_long(j) - parent_long, list_parpar_lat(j) - parent_lat];
        list_cosphi = (x * y.') / (norm(x) * norm(y));
    end
    cosphi = min(list_cosphi);
    distance = norm([LONGITUDE(index_total(i)) - parent_long,...
                                    LATITUDE(index_total(i)) - parent_lat]);
    if distance >= threshold_down && distance <= threshold_up && cosphi <= th_phi
        cands = [cands index_total(i)]; %#ok<AGROW>
    end
end

if length(cands) >= depth
    index = randperm(length(cands), depth);
    index_temp = cands(index);
else
    error('Not Enough Airports!');
end

