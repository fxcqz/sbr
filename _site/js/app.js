var opts;

function draw() 
{
    jsPlumb.reset();
	
    titler  = jsPlumb.addEndpoint("box-title",{anchor:["RightMiddle"],paintStyle:{fillStyle:"#f29441"}});
    titlel = jsPlumb.addEndpoint("box-title", {anchor:["LeftMiddle"],paintStyle:{fillStyle:"#f29441"}});
    navr  = jsPlumb.addEndpoint("box-nav",{anchor:["RightMiddle"],paintStyle:{fillStyle:"#f29441"}});
    contentl   = jsPlumb.addEndpoint("box-content",{anchor:["LeftMiddle"],paintStyle:{fillStyle:"#f29441"}});
    contentr  = jsPlumb.addEndpoint("box-content",{anchor:["RightMiddle"],paintStyle:{fillStyle:"#f29441"}});
    navl = jsPlumb.addEndpoint("box-nav",{anchor:["LeftMiddle"],paintStyle:{fillStyle:"#f29441"}});

    jsPlumb.connect({ source: titler, target: navr});
    jsPlumb.connect({ source: titlel, target: contentl});
    jsPlumb.connect({ source: contentr, target: navl});
}

$(document).ready(function() 
{
    jsPlumb.Defaults.PaintStyle = {
        lineWidth: 2,
        strokeStyle: '#d93829'
    }
	
    jsPlumb.Defaults.Endpoint = [
        "Dot",
        {radius: 3}
    ];
	
    jsPlumb.Defaults.Connector = "Bezier";
	
    opts = {
        anchors: ["LeftMiddle"],
        paintStyle:{fillStyle:"#f29441"}
    };

    draw();
});

$(window).resize(draw);

