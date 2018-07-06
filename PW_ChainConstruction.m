%% read data
% lead time
leadTime = xlsread('Data Distributions_v2_YL.xlsx','Lead Time','A1:B402');
% the number of upstream suppliers for each input part for each supplier
numSuppliers = xlsread('Data Distributions_v2_YL.xlsx','Suppliers','A1:B6');
% the number of children suppliers of the root supplier (20)
numLayer2 = xlsread('Data Distributions_v2_YL.xlsx','Correlated Children','B2:B2');
% the number of parts that each supplier in layer 2 demands
numPartsLevel2 = xlsread('Data Distributions_v2_YL.xlsx','Correlated Children','D2:E103');
% the number of parts that each supplier in layer 3 and deeper layers demands
numPartsLevel3 = xlsread('Data Distributions_v2_YL.xlsx','Correlated Children','G3:H23');
%% root node / layer 1
layer1 = 0;
currentnode = 0;
cell_layer1 = cell(1,2);
cell_layer1{1,1} = 0;
cell_layer1{1,2} = [1:numLayer2];
countparts = 0;
countparts = countparts + numLayer2;
%% layer 2
layer2 = [1:numLayer2];
cell_layer2 = cell(numLayer2,2);
% parts_layers2 is an array of the number of parts that each supplier
% in layer 1 require from its upstream suppliers in layer 2
parts_layer2 = randsample(numPartsLevel2(:,1), numLayer2, true, numPartsLevel2(:,2));
% currentnode: keep track of the id number of the suppliers that we have
% used so far
currentnode = currentnode + numLayer2;
for i = 1:numLayer2
    cell_layer2{i,1} = layer2(i);
    % for each part, we sample the number of suppliers who supply the part
    % to the downstream supplier
    thisNumSuppliers = randsample(numSuppliers(:,1), parts_layer2(i), true, numSuppliers(:,2));
    cell_layer2{i,2} = cell(1,parts_layer2(i));
    for j = 1:parts_layer2(i)
        cell_layer2{i,2}{1,j} = [(currentnode + 1):(currentnode + thisNumSuppliers(j))];
        currentnode = currentnode + thisNumSuppliers(j);
    end
end
thislayer = [layer2(end):currentnode];
countparts = countparts + sum(parts_layer2);
%% layer 3 and deeper layers
cell_all_layers = cell(1);
cell_all_layers{1} = cell_layer1;
cell_all_layers{2} = cell_layer2;
index_layer = 3;
while countparts < 1000
    numthislayer = length(thislayer);
    parts_thislayer = randsample(numPartsLevel3(:,1), numthislayer, true, numPartsLevel3(:,2));
    cell_thislayer = cell(numthislayer,2);
    if sum(parts_thislayer) == 0
        for i = 1:numthislayer
            cell_thislayer{i,1} = thislayer(i);
            cell_thislayer{i,2} = -1;
        end
        cell_all_layers{index_layer} = cell_thislayer;
        break
    end
    for i = 1:numthislayer
        cell_thislayer{i,1} = thislayer(i);
        thisNumSuppliers = randsample(numSuppliers(:,1), parts_thislayer(i), true, numSuppliers(:,2));
        cell_thislayer{i,2} = cell(1,parts_thislayer(i));
        for j = 1:parts_thislayer(i)
            cell_thislayer{i,2}{1,j} = [(currentnode+1):(currentnode+thisNumSuppliers(j))];
            currentnode = currentnode + thisNumSuppliers(j);
        end
    end
    countparts = countparts + sum(parts_thislayer);
    cell_all_layers{index_layer} = cell_thislayer;
    index_layer = index_layer + 1;
    thislayer = [(thislayer(end) + 1):currentnode];
end

%% parents
arrayParents = zeros(currentnode,2);
arrayParents(:,1) = [1:currentnode];
totallayer = length(cell_all_layers);
for i = 2:totallayer
    % thiscell refers to the cell that contains information for this layer
    thiscell = cell_all_layers{i};
    % lengththiscell = the number of suppliers in this layer
    lengththiscell = length(thiscell);
    for j = 1:lengththiscell
        % parts in this layer
        parts = thiscell{j,2};
        if length(parts) ~= 0
            for k = 1:length(parts)
                thispart = parts{k};
                for l = 1:length(thispart)
                    arrayParents(thispart(l),2) = thiscell{j,1};
                end
            end
        end
    end
end
%% create the output text file
%% root node
fileID = fopen('PW_Chain_text.txt','w');
line_vector = [];
index = 1;
for i = 1:numLayer2
    line_vector(index) = i;
    line_vector(index+1) = 1; % fraction
    line_vector(index+2) = 1; % demand quantity
    index = index + 3;
end
line_string = strjoin(arrayfun(@(x) num2str(x), line_vector,'UniformOutput',false),',');
fprintf(fileID, ['0,-1,-1,-1,' line_string '\n']);
disp('done')
%% the rest
for i = 2:length(cell_all_layers)
    thislayer = cell_all_layers{i};
    for j = 1:length(thislayer)
        line_vector = [];
        index = 1;
        line_vector(index) = thislayer{j,1};
        line_vector(index+1) = -1; %latitude
        line_vector(index+2) = -1; %longitude
        line_vector(index+3) = arrayParents(thislayer{j,1}, 2);
        index = index + 4;
        parts = thislayer{j,2};
        if length(parts) ~= 0
            for k = 1:length(parts)
                thispart = parts{k};
                nonzero = randsample(length(thispart), 1);
                for l = 1:length(thispart)
                    line_vector(index) = thispart(l);
                    if l == nonzero
                        line_vector(index+1) = 1;
                    else
                        line_vector(index+1) = 0;
                    end
                    index = index + 2;
                end
                line_vector(index) = 1;
                index = index + 1;
            end
        else
            line_vector(index) = -1;
            index = index + 1;
        end
        line_string = strjoin(arrayfun(@(x) num2str(x), line_vector,'UniformOutput',false),',');
        fprintf(fileID, [line_string '\n']);
    end
end
disp('done')
%% leaf nodes
for i = (thislayer{j,1}+1):currentnode
    line_vector = [];
    line_vector(1) = i;
    line_vector(2) = -1;
    line_vector(3) = -1;
    line_vector(4) = -1;
    line_string = strjoin(arrayfun(@(x) num2str(x), line_vector,'UniformOutput',false),',');
    fprintf(fileID, [line_string '\n']);
end
disp('done')

%% plot graph
% recipient
s = [];
% supplier
t = [];
for i = 1:length(arrayParents)
    s = [s arrayParents(i,2)];
    t = [t arrayParents(i,1)];
end
G = digraph;
G = addedge(G, cellstr(string(t)), cellstr(string(s)));
f2 = figure;
set(f2, 'Position', [400, 90, 5000, 1420]);
p1 = plot(G, '-o', 'Linewidth', 1,  'MarkerSize', 3,'Layout', 'layered', 'ArrowSize', 3);
labelnode(p1, arrayfun(@(x) num2str(x), 0:currentnode,'UniformOutput',false), arrayfun(@(x) num2str(x), 0:currentnode,'UniformOutput',false));
grid on; box on;
axis tight;
set(gca, 'xtick', []);
set(gca, 'ytick', []);
tightfig(f2);

%% extract the number of parts in each layer
numparts_eachlayer = zeros(1,length(cell_all_layers));
for i = 1:length(cell_all_layers)
    thislayer = cell_all_layers{i};
    count = 0;
    for j = 1:size(thislayer,1)
        count = count + length(thislayer{j,2});
    end
    numparts_eachlayer(i) = count;
end
%% plot
figure
plot((1:length(cell_all_layers)),numparts_eachlayer)
title('The number of parts in each layer')
xlabel('layer')
ylabel('the number of parts')
text1 = ['Number of part types: ' num2str(sum(numparts_eachlayer))];
text2 = ['Number of layers: ' num2str(length(cell_all_layers))];
text(3,600, text1)
text(3,500, text2)