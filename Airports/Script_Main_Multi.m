%%
clear all; %#ok<CLALL>
close all;
%%
% Load Airport Data...
load('Airports.mat');
total = length(LATITUDE);
index_total = 1 : total;
% Plot Map...
f1 = figure;
set(f1, 'Position', [160, 90, 2800, 1420]);
axis([-200 200 -100 100]);
geoshow('landareas.shp', 'FaceColor', [0 0 0]);
hold('on');
title('Supply Chain Network on the Map', 'interpreter', 'latex','fontsize', 22);
xlabel('Longitude', 'interpreter', 'latex','fontsize', 22);
ylabel('Latitude', 'interpreter', 'latex','fontsize', 22);
grid on; box on;
tightfig(f1);
%% Define Variables
% Length of Chain (Depth of the Supply Chain Tree): 4
% Define minimum-maximum numbers of possible children in each depth...
depth_1 = 20; 
depth_min_2 = 4;
depth_max_2 = 8;
depth_min_3 = 2;
depth_max_3 = 4;

group_size_min_1 = 2; 
group_size_max_1 = 4;
group_size_min_2 = 2;
group_size_max_2 = 4;
group_size_min_3 = 1;
group_size_max_3 = 3;

demand_min_1 = 10;
demand_max_1 = 20;
demand_min_2 = 10;
demand_max_2 = 20;
demand_min_3 = 10;
demand_max_3 = 20;

commonparts_2 = 4;
commonparts_3 = 10;

sharingparts_min_2 = 3;
sharingparts_max_2 = 6;
sharingparts_min_3 = 3;
sharingparts_max_3 = 6;

sharing_rate_2 = 0.2;
sharing_rate_3 = 0.2;
%% Define variables for plotting
% For plotting...
head_length = 10;
head_width = 10;
line_width = 1.5;
marker_size = 40;
arrow_size = 12;
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% ROOT...
% Choose the location of the root, at random...
root_index = randperm(total, 1);
% Put it on the map...
plot(LONGITUDE(root_index), LATITUDE(root_index), 'sy', 'MarkerSize', 40, 'MarkerFaceColor', 'y');
% Remove this node from the remaining list...
total_rem = total - 1;
index_total(root_index) = [];
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Next Layer of the Tree...
% Choose the location of the nodes of Layer 1...
index_temp_1 = sample_dense(LATITUDE(root_index), LONGITUDE(root_index),...
                        LATITUDE, LONGITUDE,...
                        depth_1, total_rem, index_total, 30);
%% modification
unchosen = length(index_temp_1);
length1 = length(index_temp_1);
children_line_1 = [];
while unchosen > 0
    % sample the group size
    % group size refers to the number of suppliers that supply the same
    % type of components to the root
    group_size = randsample((group_size_min_1:group_size_max_1),1);
    % if we have too few airports (suppliers) remain unchosen
    if unchosen < group_size
        if unchosen < group_size_min_1
            % so few that it is smaller than the minimum number of
            % suppliers to supply a particular type of components to the
            % root
            break;
        else
            group_size = unchosen;
        end
    end
    % sample the fractions
    n_nums = rand(1, group_size);
    fractions = n_nums/sum(n_nums);
    % sample quantity
    quant = randi([group_size*demand_min_1 group_size*demand_max_1]);
    line_temp = [index_temp_1((length1 - unchosen + 1):(length1 - unchosen + group_size)); fractions];
    line_temp = line_temp(:).';
    children_line_1 = [children_line_1 line_temp quant];
    unchosen = unchosen - group_size;
end
index_temp_1 = index_temp_1(1:(length1 - unchosen));
depth_1 = length(index_temp_1);
%%%% this stays the same even when a supplier has multiple customers since
%%%% in the first layer, there is always only one root.
%%
index_total(ismember(index_total, index_temp_1)) = [];
total_rem = total_rem - depth_1;
% Put them on the map...
plot(LONGITUDE(index_temp_1), LATITUDE(index_temp_1), '.r', 'MarkerSize', marker_size);
% Put the arrows on the map...
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Layer 1
%depth_2 = zeros(1, depth_1);
index_2 = []; % list of unique IDs of nodes in layer 2
index_temp_2 = cell(1, depth_1); % list of id's belonged to each parent node in layer 1
index_parents_2 = cell(1,1); % list of parent's IDs corresponding to nodes in index_2 at the same array index

%indices of nodes in layer2, divided into subgroups of each parent node in layer 1
index_subgroups_2 = cell(1, depth_1); 
%number of subgroups in layer 2, these subgroups belong to each parent
%node in layer 1
num_subgroups_2 = zeros(1, depth_1);
children_line_2 = cell(1, depth_1);

depth_2 = zeros(1, depth_1);
current_index = 0;
for i = 1 : depth_1
    line2arrow(plot(LONGITUDE([index_temp_1(i) root_index]),...
                     LATITUDE([index_temp_1(i) root_index]),'-r', 'Linewidth', line_width),...
                     'HeadLength', head_length, 'HeadWidth', head_length);
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Next Layer of the Tree...
    depth_temp_2 = randi([depth_min_2 depth_max_2], 1);
    % Choose the location of the nodes of Layer 2...
    %index_2{i} = randperm(total_rem, depth_2(i));
    index_temp_2{i} = sample_sparse(LATITUDE(index_temp_1(i)), LONGITUDE(index_temp_1(i)),...
                                    LATITUDE(root_index), LONGITUDE(root_index),...
                                    LATITUDE, LONGITUDE,...
                                    depth_temp_2, total_rem, index_total, 20, 100, -0.2);
    %index_temp_2{i} = index_total(index_2{i});
    %% modification for the scenario where each type of components 
    %can be supplied by multiple suppliers to one manufacturer
    unchosen = length(index_temp_2{i});
    length2 = length(index_temp_2{i});
    line_temp_2 = [];
    num_subgroup = 0;
    index_subgroups_2{i} = cell(1, 1);
    while unchosen > 0
        group_size = randsample((group_size_min_2:group_size_max_2),1);
        if unchosen < group_size
            if unchosen < group_size_min_2
                break;
            else
                group_size = unchosen;
            end
        end
        num_subgroup = num_subgroup + 1;
        index_thissubgroup = index_temp_2{i}((length2 - unchosen + 1):(length2 - unchosen + group_size));
        index_subgroups_2{i}{num_subgroup} = index_thissubgroup;
        index_2 = [index_2 index_thissubgroup];
        unchosen = unchosen - group_size;
    end
    num_subgroups_2(i) = num_subgroup;
    index_temp_2{i} = index_temp_2{i}(1:(length2 - unchosen));
    depth_temp_2 = length2 - unchosen;
    total_rem = total_rem - depth_temp_2;
    for j = (current_index + 1):(current_index + depth_temp_2)
        index_parents_2{j} = index_temp_1(i);
    end
    current_index = current_index + depth_temp_2;
    index_total(ismember(index_total, index_temp_2{i})) = [];
    depth_2(i) = depth_temp_2;
end
%% modification for the scenario where each supplier can supply 
%more than one manufacturer
%% common parts
notenough_supplygroups = true;
%indices of the manufacturers in layer 1 that demand the same components 
while notenough_supplygroups
    index_sharing_1 = cell(1, commonparts_2);
    sharing_size_1 = ones(1, commonparts_2);
    thislength = 0;
    for i = 1:commonparts_2
        sharing_size = randsample((sharingparts_min_2:sharingparts_max_2), 1);
        thislength = thislength + sharing_size;
        index_sharing_1{i} = randsample(depth_1, sharing_size);
        sharing_size_1(i) = sharing_size;
    end
    % collect the indices from the cell array to a list array
    list_index_sharing = zeros(1, thislength);
    current_index = 1;
    for i = 1:commonparts_2
        for j = 1:sharing_size_1(i)
            list_index_sharing(current_index) = index_sharing_1{i}(j);
            current_index = current_index + 1;
        end
    end
    % check if each manufacturer has enough supply groups
    [u1, u2, u3] = unique(list_index_sharing);
    countmatrix = [u1.', accumarray(u3,1)];
    notenough_supplygroups = false;
    for i = 1:size(countmatrix,1)
        %if any manufacturer requires higher number of components than the
        %number of supplier groups that it has
        %then we want to regenerate/resample the partition above
        if countmatrix(i,2) > num_subgroups_2(countmatrix(i,1))
            notenough_supplygroups = true;
        end
    end
end
%% allocate additional suppliers to manufacturers that require common parts
% when we allocate, we go through each common part
% For instance, common part 1 is required by 3 manufacturers in layer 1,
% which are the manufacturers no. 2, 5 and 11 in layer 1.
% Now we look at the subgroup of suppliers in layer 2 of each manufacturer
% in layer 1.
% We take the first supplier subgroup of manu 2,5 and 11 to be the
% suppliers of the first common part. We will record in checked_subgroups
% variable about how far we have checked / how many subgroups of each
% manufacturer we have checked. 
checked_subgroups = ones(1, depth_1);
for i = 1:commonparts_2 %4
    supply_index = cell(1, sharing_size_1(i));
    for j = 1:sharing_size_1(i) %3
        for k = 1:sharing_size_1(i) %3
            if j ~= k
                idx_1 = index_sharing_1{i}(k);
                supply_index{j} = [supply_index{j} index_subgroups_2{idx_1}{checked_subgroups(idx_1)}];
            end
        end
    end
    for j = 1:sharing_size_1(i)
        % Each supplier, that has not been assigned to this manufucturer
        % yet, have a certain, fixed chance of being assigned to the
        % manufacturer.
        idx_1 = index_sharing_1{i}(j);
        additional_suppliers = supply_index{j}(rand(1, size(supply_index{j},2)) < sharing_rate_2);
        % append them to the list of suppliers that we assigned earlier
        index_subgroups_2{idx_1}{checked_subgroups(idx_1)} = ...
            [index_subgroups_2{idx_1}{checked_subgroups(idx_1)} additional_suppliers];
        checked_subgroups(idx_1) = checked_subgroups(idx_1) + 1;
        index_temp_2{idx_1} = [index_temp_2{idx_1} additional_suppliers];
        depth_2(idx_1) = depth_2(idx_1) + length(additional_suppliers);
        for k = 1:length(additional_suppliers)
            idx_add = find(index_2 == additional_suppliers(k));
            index_parents_2{idx_add} = [index_parents_2{idx_add} index_temp_1(idx_1)];
        end
    end
end

%% make the printed lines for layer 1
for i = 1:depth_1
    for j = 1:num_subgroups_2(i)
        group_size = size(index_subgroups_2{i}{j}, 2);
        n_nums = rand(1, group_size);
        fractions = n_nums/sum(n_nums);
        quant = randi([group_size*demand_min_2 group_size*demand_max_2]);
        line_temp = [index_subgroups_2{i}{j}; fractions];
        children_line_2{i} = [children_line_2{i} line_temp(:).' quant];
    end
end
%% draw on the map
for i = 1:depth_1
    % Put them on the map...
    plot(LONGITUDE(index_temp_2{i}), LATITUDE(index_temp_2{i}), '.g', 'MarkerSize', marker_size);
    % Put the arrows on the map...
    for j = 1 : depth_2(i)
        line2arrow(plot(LONGITUDE([index_temp_2{i}(j) index_temp_1(i)]),...
                     LATITUDE([index_temp_2{i}(j) index_temp_1(i)]), '-g', 'Linewidth', line_width),...
                     'HeadLength', head_length, 'HeadWidth', head_length);
    end
end
%% Layer 2
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
index_3 = []; % list of unique ID's of nodes in layer 3
depth_2_total = length(index_2); % number of nodes in layer 2 (parent nodes of nodes layer 3)
index_temp_3 = cell(1, depth_2_total); % indices of nodes in each subgroup of each node in layer 2 (indices of layer 3 grouped by subgroups)
index_parents_3 = cell(1,1); % indices of parent nodes (in layer 2) of nodes in layer 3
index_subgroups_3 = cell(1,depth_2_total); % indices of node in layer 3, grouped by subgroups in each node in layer 2
num_subgroups_3 = zeros(1, depth_2_total); % number of subgroups of each node in layer 2
children_line_3 = cell(1, depth_2_total); % printing lines
depth_3 = zeros(1, depth_2_total); % number of children nodes in layer 3 of each node in layer 2
current_index = 0;
%%
for i = 1:depth_2_total
    depth_temp_3 = randi([depth_min_3 depth_max_3], 1);
    %%% this sample sparse line still needs to be fixed
    index_temp_3{i} = sample_sparse_multiparents(LATITUDE(index_2(i)), LONGITUDE(index_2(i)),...
                                            LATITUDE(index_parents_2{i}), LONGITUDE(index_parents_2{i}),...
                                            LATITUDE, LONGITUDE,...
                                            depth_temp_3, total_rem, index_total, 0, 300, 0.4);
    %% modification
    unchosen = length(index_temp_3{i});
    length3 = length(index_temp_3{i});
    num_subgroup = 0;
    while unchosen > 0
        group_size = randsample((group_size_min_3:group_size_max_3), 1);
        if unchosen < group_size 
            if unchosen < group_size_min_3
                break;
            else
                group_size = unchosen;
            end
        end
        num_subgroup = num_subgroup + 1;
        index_thissubgroup = index_temp_3{i}((length3 - unchosen + 1):(length3 - unchosen + group_size));
        index_subgroups_3{i}{num_subgroup} = index_thissubgroup;
        index_3 = [index_3 index_thissubgroup];
        unchosen = unchosen - group_size;
    end
    num_subgroups_3(i) = num_subgroup;
    depth_temp_3 = length3 - unchosen;
    index_temp_3{i} = index_temp_3{i}(1:depth_temp_3);
    total_rem = total_rem - depth_temp_3;
    for j = (current_index + 1):(current_index + depth_temp_3)
        index_parents_3{j} = index_2(i);
    end
    current_index = current_index + depth_temp_3;
    index_total(ismember(index_total, index_temp_3{i})) = [];
    depth_3(i) = depth_temp_3;
end

%% modification for the scenario where each supplier can supply 
%more than one manufacturer
%% common parts
notenough_supplygroups = true;
%indices of the manufacturers in layer 2 that demand the same components 
while notenough_supplygroups
    index_sharing_2 = cell(1, commonparts_3); %indices (order, not the actual index) of parent nodes in layer 2 that require the same supplies from suppliers in layer 3
    sharing_size_2 = ones(1, commonparts_3); %number of parent nodes in layer 2 that require each "common part"
    thislength = 0;
    for i = 1:commonparts_3
        sharing_size_2(i) = randsample((sharingparts_min_3:sharingparts_max_3), 1);
        thislength = thislength + sharing_size_2(i);
        index_sharing_2{i} = randsample(depth_2_total, sharing_size_2(i));
    end
    % collect the indices from the cell array to a list array
    list_index_sharing = zeros(1, thislength);
    current_index = 1;
    for i = 1:commonparts_3
        for j = 1:sharing_size_2(i)
            list_index_sharing(current_index) = index_sharing_2{i}(j);
            current_index = current_index + 1;
        end
    end
    % check if each manufacturer has enough supply groups
    [u1, u2, u3] = unique(list_index_sharing);
    countmatrix = [u1.', accumarray(u3,1)];
    notenough_supplygroups = false;
    for i = 1:size(countmatrix,1)
        %if any manufacturer requires higher number of components than the
        %number of supplier groups that it has
        %then we want to regenerate/resample the partition above
        if countmatrix(i,2) > num_subgroups_3(countmatrix(i,1))
            notenough_supplygroups = true;
        end
    end
end

%% allocate additional suppliers to manufacturers that require common parts
% when we allocate, we go through each common part
% For instance, common part 1 is required by 3 manufacturers in layer 1,
% which are the manufacturers no. 2, 5 and 11 in layer 1.
% Now we look at the subgroup of suppliers in layer 2 of each manufacturer
% in layer 1.
% We take the first supplier subgroup of manu 2,5 and 11 to be the
% suppliers of the first common part. We will record in checked_subgroups
% variable about how far we have checked / how many subgroups of each
% manufacturer we have checked. 
checked_subgroups = ones(1, depth_2_total);
for i = 1:commonparts_3 %4
    supply_index = cell(1, sharing_size_2(i));
    for j = 1:sharing_size_2(i) %3
        for k = 1:sharing_size_2(i) %3
            if j ~= k
                idx_1 = index_sharing_2{i}(k);
                supply_index{j} = [supply_index{j} index_subgroups_3{idx_1}{checked_subgroups(idx_1)}];
            end
        end
    end
    for j = 1:sharing_size_2(i)
        % Each supplier, that has not been assigned to this manufucturer
        % yet, have a certain, fixed chance of being assigned to the
        % manufacturer.
        idx_1 = index_sharing_2{i}(j);
        additional_suppliers = supply_index{j}(rand(1, size(supply_index{j},2)) < sharing_rate_3);
        % append them to the list of suppliers that we assigned earlier
        index_subgroups_3{idx_1}{checked_subgroups(idx_1)} = ...
            [index_subgroups_3{idx_1}{checked_subgroups(idx_1)} additional_suppliers];
        checked_subgroups(idx_1) = checked_subgroups(idx_1) + 1;
        index_temp_3{idx_1} = [index_temp_3{idx_1} additional_suppliers];
        depth_3(idx_1) = depth_3(idx_1) + length(additional_suppliers);
        for k = 1:length(additional_suppliers)
            idx_add = find(index_3 == additional_suppliers(k));
            index_parents_3{idx_add} = [index_parents_3{idx_add} index_2(idx_1)];
        end
    end
end

%% make the printed lines for layer 1
for i = 1:depth_2_total
    for j = 1:num_subgroups_3(i)
        group_size = size(index_subgroups_3{i}{j}, 2);
        n_nums = rand(1, group_size);
        fractions = n_nums/sum(n_nums);
        quant = randi([group_size*demand_min_3 group_size*demand_max_3]);
        line_temp = [index_subgroups_3{i}{j}; fractions];
        children_line_3{i} = [children_line_3{i} line_temp(:).' quant];
    end
end

%% drawing on the map
for i = 1:depth_2_total
    % Put them on the map...
    plot(LONGITUDE(index_temp_3{i}), LATITUDE(index_temp_3{i}), '.c', 'MarkerSize', marker_size);
    for j = 1 : depth_3(i)
        line2arrow(plot(LONGITUDE([index_temp_3{i}(j) index_2(i)]),...
                     LATITUDE([index_temp_3{i}(j) index_2(i)]), '-c', 'Linewidth', line_width),...
                     'HeadLength', head_length, 'HeadWidth', head_length);
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    end       
end
% Remove these nodes from the remaining list...

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
fileID = fopen('Chain.txt','w');
% Write the root in file...
%%%%%%%%%%%%%%%%%
line_vector = [root_index...
               LATITUDE(root_index)...
               LONGITUDE(root_index)...
               -1 children_line_1];
line_string = strjoin(arrayfun(@(x) num2str(x), line_vector,'UniformOutput',false),',');
fprintf(fileID, [line_string '\n']);
% Write depth 1 in file...
for i = 1 : depth_1
    parent = root_index;
    line_vector = [index_temp_1(i)...
                   LATITUDE(index_temp_1(i))...
                   LONGITUDE(index_temp_1(i))...
                   parent children_line_2{i}];
    line_string = strjoin(arrayfun(@(x) num2str(x), line_vector,'UniformOutput',false),',');
    fprintf(fileID, [line_string '\n']);
end
% Write depth 2 in file...
for i = 1 : depth_2_total
    parent = index_parents_2{i};
    line_vector = [index_2(i) LATITUDE(index_2(i)) LONGITUDE(index_2(i)) parent children_line_3{i}];
    line_string = strjoin(arrayfun(@(x) num2str(x), line_vector, 'UniformOutput', false), ',');
    fprintf(fileID, [line_string '\n']);
end
% Write depth 3 in file...
for i = 1 : length(index_3)
    parent = index_parents_3{i};
    line_vector = [index_3(i) LATITUDE(index_3(i)) LONGITUDE(index_3(i)) parent -1];
    line_string = strjoin(arrayfun(@(x) num2str(x), line_vector,'UniformOutput',false),',');
    fprintf(fileID, [line_string '\n']);
end    
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Plot Graph...
number_allparents = 0;
number_allparents = number_allparents + depth_1;
for i = 1:depth_2_total
    number_allparents = number_allparents + length(index_parents_2{i});
end
disp('1')
for i = 1:length(index_3)
    number_allparents = number_allparents + length(index_parents_3{i});
end
s = zeros(1, number_allparents); %parents
t = zeros(1, number_allparents); %children
current_index = 1;
disp('2')
for i = 1:depth_1
    s(current_index) = root_index;
    t(current_index) = index_temp_1(i);
    current_index = current_index + 1;
end
disp('3')
for i = 1:depth_2_total
    child = index_2(i);
    parents = index_parents_2{i};
    for j = 1:length(parents)
        s(current_index) = parents(j);
        t(current_index) = child;
        current_index = current_index + 1;
    end
end
disp('4')
for i = 1:length(index_3)
    child = index_3(i);
    parents = index_parents_3{i};
    for j = 1:length(parents)
        s(current_index) = parents(j);
        t(current_index) = child;
        current_index = current_index + 1;
    end
end
disp('5')
%%
%G = digraph(s(1:20),t(1:20));
G = digraph;
G = addedge(G, cellstr(string(t)), cellstr(string(s)));
f2 = figure;
set(f2, 'Position', [160, 90, 2800, 1420]);
plot(G, '-o', 'Linewidth', 3,  'MarkerSize', 10, 'NodeLabel', CITY(str2num(char(table2array(G.Nodes)))),...
                                                                                                                                                        'Layout', 'layered', 'ArrowSize', arrow_size); %#ok<ST2NM>
grid on; box on;
axis tight;
set(gca, 'xtick', []);
set(gca, 'ytick', []);
tightfig(f2);