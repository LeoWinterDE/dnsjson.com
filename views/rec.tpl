% include('global/header.tpl', title=name)
<div class="container">
    <div class="starter-template">
        <div class="well well-lg">
            <h1>{{name}} ({{type}})</h1>
            <p id="counterVal" style="font-size: 42px;">
                <pre>
% for rec in records:
    {{rec}}
% end
</pre>
            </p>
        </div>
        
        <div class="panel panel-primary">
            <div class="panel-heading">
                <h3 class="panel-title">Need to script it?</h3>
            </div>
            <div class="panel-body">
                <p>
                Verify the results using curl:
                </p>
                <pre>curl -X GET https://dnsjson.com/{{name}}/{{type}}.json</pre>
            </div>
        </div>
    </div>
</div>
% include('global/footer.tpl')