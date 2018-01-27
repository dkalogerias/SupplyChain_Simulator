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
% Length of Chain (Depth of the Supply Chain Tree): 4
% Define minimum-maximum numbers of possible children in each depth...
depth_1 = 20;
depth_min_2 = 4;
depth_max_2 = 8;
depth_min_3 = 2;
depth_max_3 = 4;
%depth_min_4 = 1;
%depth_max_4 = 2;
% For plotting...
head_length = 10;
head_width = 10;
line_width = 1.5;
marker_size = 40;
arrow_size = 12;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
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
index_total(ismember(index_total, index_temp_1)) = [];
total_rem = total_rem - depth_1;
% Put them on the map...
plot(LONGITUDE(index_temp_1), LATITUDE(index_temp_1), '.r', 'MarkerSize', marker_size);
% Put the arrows on the map...
%depth_2 = zeros(1, depth_1);
index_2 = cell(1, depth_1);
index_temp_2 = cell(1, depth_1);
index_temp_3 = cell(1, depth_1);
for i = 1 : depth_1
    line2arrow(plot(LONGITUDE([index_temp_1(i) root_index]),...
                     LATITUDE([index_temp_1(i) root_index]),'-r', 'Linewidth', line_width),...
                     'HeadLength', head_length, 'HeadWidth', head_length);
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Next Layer of the Tree...
    depth_2 = randi([depth_min_2 depth_max_2], 1);
    % Choose the location of the nodes of Layer 2...
    %index_2{i} = randperm(total_rem, depth_2(i));
    index_temp_2{i} = sample_sparse(LATITUDE(index_temp_1(i)), LONGITUDE(index_temp_1(i)),...
                                    LATITUDE(root_index), LONGITUDE(root_index),...
                                    LATITUDE, LONGITUDE,...
                                    depth_2, total_rem, index_total, 20, 100, -0.2);
    %index_temp_2{i} = index_total(index_2{i});
    index_total(ismember(index_total, index_temp_2{i})) = [];
    total_rem = total_rem - depth_2;
    % Put them on the map...
    plot(LONGITUDE(index_temp_2{i}), LATITUDE(index_temp_2{i}), '.g', 'MarkerSize', marker_size);
    % Put the arrows on the map...
    index_temp_3{i} = cell(1, depth_2);
    for j = 1 : depth_2
        line2arrow(plot(LONGITUDE([index_temp_2{i}(j) index_temp_1(i)]),...
                     LATITUDE([index_temp_2{i}(j) index_temp_1(i)]), '-g', 'Linewidth', line_width),...
                     'HeadLength', head_length, 'HeadWidth', head_length);
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Next Layer of the Tree...
        depth_3 = randi([depth_min_3 depth_max_3], 1);
        % Choose the location of the nodes of Layer 3...
        index_temp_3{i}{j} = sample_sparse(LATITUDE(index_temp_2{i}(j)), LONGITUDE(index_temp_2{i}(j)),...
                                            LATITUDE(index_temp_1(i)), LONGITUDE(index_temp_1(i)),...
                                            LATITUDE, LONGITUDE,...
                                            depth_3, total_rem, index_total, 0, 300, 0.4);
        index_total(ismember(index_total, index_temp_3{i}{j})) = [];
        total_rem = total_rem - depth_3;
        % Put them on the map...
        plot(LONGITUDE(index_temp_3{i}{j}), LATITUDE(index_temp_3{i}{j}), '.c', 'MarkerSize', marker_size);
        for k = 1 : depth_3
            line2arrow(plot(LONGITUDE([index_temp_3{i}{j}(k) index_temp_2{i}(j)]),...
                         LATITUDE([index_temp_3{i}{j}(k) index_temp_2{i}(j)]), '-c', 'Linewidth', line_width),...
                         'HeadLength', head_length, 'HeadWidth', head_length);
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
       end
    end        
end
% Remove these nodes from the remaining list...
%total_rem = total_rem - depth_1;
%index_total = index_total(index_total ~= index_1);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
fileID = fopen('Chain.txt','w');
% Write the root in file...
demand_min_1 = 10;
demand_max_1 = 20;
demand_min_2 = 10;
demand_max_2 = 20;
demand_min_3 = 10;
demand_max_3 = 20;
%%%%%%%%%%%%%%%%%
childrenANDdemands = [index_temp_1; randi([demand_min_1 demand_max_1], 1,  length(index_temp_1))];
childrenANDdemands = childrenANDdemands(:).';
line_vector = [root_index...
               LATITUDE(root_index)...
               LONGITUDE(root_index)...
               -1 childrenANDdemands];
line_string = strjoin(arrayfun(@(x) num2str(x), line_vector,'UniformOutput',false),',');
fprintf(fileID, [line_string '\n']);
% Write depth 1 in file...
for i = 1 : length(index_temp_1)
    parent = root_index;
    childrenANDdemands = [index_temp_2{i}; randi([demand_min_2 demand_max_2], 1,  length(index_temp_2{i}))];
    childrenANDdemands = childrenANDdemands(:).';
    line_vector = [index_temp_1(i)...
                   LATITUDE(index_temp_1(i))...
                   LONGITUDE(index_temp_1(i))...
                   parent childrenANDdemands];
    line_string = strjoin(arrayfun(@(x) num2str(x), line_vector,'UniformOutput',false),',');
    fprintf(fileID, [line_string '\n']);
end
% Write depth 2 in file...
for i = 1 : length(index_temp_1)
    parent = index_temp_1(i);
    for j = 1 : length(index_temp_2{i})
        childrenANDdemands = [index_temp_3{i}{j}; randi([demand_min_3 demand_max_3], 1,  length(index_temp_3{i}{j}))];
        childrenANDdemands = childrenANDdemands(:).';
        line_vector = [index_temp_2{i}(j)...
                       LATITUDE(index_temp_2{i}(j))...
                       LONGITUDE(index_temp_2{i}(j))...
                       parent childrenANDdemands];
        line_string = strjoin(arrayfun(@(x) num2str(x), line_vector,'UniformOutput',false),',');
        fprintf(fileID, [line_string '\n']);
    end
end
% Write depth 3 in file...
for i = 1 : length(index_temp_1)
    for j = 1 : length(index_temp_2{i})
        parent = index_temp_2{i}(j);
        for k = 1 : length(index_temp_3{i}{j})
            line_vector = [index_temp_3{i}{j}(k)...
                           LATITUDE(index_temp_3{i}{j}(k))...
                           LONGITUDE(index_temp_3{i}{j}(k))...
                           parent -1];
            line_string = strjoin(arrayfun(@(x) num2str(x), line_vector,'UniformOutput',false),',');
            fprintf(fileID, [line_string '\n']);
        end
    end
end    
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Plot Graph...
s = root_index * ones(1, length(index_temp_1));
t = index_temp_1;
for i = 1 : length(index_temp_1)
    s = [s index_temp_1(i)*ones(1, length(index_temp_2{i}))];
    t = [t index_temp_2{i}]; %#ok<*AGROW>
    for j = 1 : length( index_temp_2{i})
        s = [s index_temp_2{i}(j)*ones(1, length(index_temp_3{i}{j}))];
        t = [t index_temp_3{i}{j}];
    end        
end
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




                                                                                                             
