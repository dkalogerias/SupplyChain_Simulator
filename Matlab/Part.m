% Create a class for Suppliers...
classdef Part
    % Defining properties for each Supplier...
    properties
        From                % Identification Key for Part...
        To                  % Same...
        Shipped             % Shipped or in still in inventory? Boolean...
        DayCounter          % If shipped, days remainining until arrival...        
    end
    % Methods
    methods
        function obj = Supplier(From, To)
            obj.From = From;
            obj.To = To;
            obj.Shipped = 0;
            obj.DayCounter = -1;
        end
    end
end