Array.prototype.insert = function(index, item) {
	this.splice(index, 0, item);
};

Array.prototype.foreach = function(f, arg) {
	for (var i = 0; i < this.length; i += 1) {
		var fr = f(i, this[i], arg)
		if (undefined != fr)
			return fr
	}
}

treeTool = {
	treeRootId : 0,
	isNew : true,
	nid : -1,
	isInitTree: false,
	datas:null,
	getTreeNodeData : function(fnid) {
		var nodesData = CTestPlanAPi.getCtreeRoot(fnid)
		for ( var i in nodesData) {
			var n = nodesData[i]
			n['text'] = n['name']
			n['state'] = 'closed'
		}
		return nodesData
	},
	initTree : function() {
		var condition = DataOperation.GetCondition()
		var tdata = treeTool.getTreeNodeData(treeTool.treeRootId)
		if(tdata.length>0 && !treeTool.treeRootNodeId)
			treeTool.treeRootNodeId = tdata[0].nid
		$('#folder-list').tree({
			animate : true,
			data : tdata,
			onSelect : function(node){
				if(treeTool.isInitTree){
					treeTool.setNodeLayer(node)
					treeTool.tree = node
					$(this).tree('expand', node.target)
				}else{
					var p = node
					var tn = []
					while(p){
						tn.insert(0,p.nid)
						p = $(this).tree('getParent',p.target)
					}
					window.location.href = window.location.pathname + "#tree=" + tn.join(",")
					condition = DataOperation.GetCondition()
					treeTool.expandTree(condition.tree)
				}
			},
			onDblClick : function(node) {
				treeTool.setNodeLayer(node)
				if (node.state == "open")
					$(this).tree('collapse', node.target)
				else
					$(this).tree('expand', node.target)
			},
			onBeforeExpand : function(node) {
				if (node.children == undefined)
					$(this).tree('append', {
						parent : node.target,
						data : treeTool.getTreeNodeData(node.nid)
					});
			},
			onContextMenu : function(e, node) {
				e.preventDefault();
				treeTool.tree = node
				if (treeTool.isTestPlan)
					$('#treePlanMenu').menu('show', {
						left : e.pageX,
						top : e.pageY
					});
				else
					$('#treeMenu').menu('show', {
						left : e.pageX,
						top : e.pageY
					});
			},
			onLoadSuccess: function(){
				if(!condition.tree&&treeTool.treeRootNodeId)
					condition.tree = "" + treeTool.treeRootNodeId
				if(condition.tree){
					setTimeout(treeTool.expandTree, 2, condition.tree)
				}
			}
		})
	},
	expandTree: function(treeNodes){
		var ftr = $('#folder-list')
		var targets = ftr.tree("getRoots")
		treeTool.isInitTree = true
		treeNodes.split(",").foreach( function(i,nid){
			targets.foreach(function(i,node){
				if(nid == ""+node.nid){
					ftr.tree("select", node.target)
					targets = ftr.tree("getChildren",node.target)
				}
			})
		})
		setTimeout(treeDataTool.loadTreeDataList,1)
		treeTool.isInitTree = false
	},
	setNodeLayer: function(node){
		var pnode = $('#folder-list').tree('getParent',node.target)
		if(pnode){
			node.tlayer = pnode.tlayer+1
			if(node.tlayer==2)
				treeTool.nid2 = node.nid
		}else{
			treeTool.nid1 = node.nid
			treeTool.nid2 = undefined
			node.tlayer = 1
		}
	},
	deleteTreeNode : function() {
		$.messager.confirm('目录', '确定删除目录', function(r){
			if (r){
				CTestPlanAPi.deleteCtree(treeTool.tree.nid)
				treeTool.initTree()
			}
		});
	},
	showTreeNode : function(isNew) {
		$('#treeAdd').dialog('open')
		if (isNew)
			$("#treeName").val("")
		else
			$("#treeName").val(treeTool.tree.name)
		treeTool.isNew = isNew
		var fnid = treeTool.nid
	},
	warnSelectRoot: function(isHidMsg){
		var n = $('#folder-list').tree('getSelected');
		if(!isHidMsg && n.nid == treeTool.treeRootNodeId)
			$.messager.alert("提醒", '您当前选择的是：<strong>根目录</strong>' +n.name+"，也可参考建议:<br>  1. 选择非根目录，新增  <br>2. 或选择目录后右键，选择新增");
		return n.name
	},
	saveTreeNode : function() {
		var name = $("#treeName").val()
		if(isRootTree.checked){
			CTestPlanAPi.saveCtree(name, treeTool.treeRootId)
		}
		else if (treeTool.isNew)
			CTestPlanAPi.saveCtree(name, treeTool.tree ? treeTool.tree.nid : treeTool.treeRootId)
		else
			CTestPlanAPi.saveCtree(name, treeTool.tree.fnid, treeTool.tree.nid)
		$('#treeAdd').dialog('close')
		treeTool.initTree()
	},
	getDataByName: function(datas, name, value){
		if(value)
			for (var i = 0; i < datas.total; i += 1) {
				var dataRow = datas.rows[i]
				if (parseInt(dataRow[name]) == parseInt(value)){
						return dataRow
				}
			}
	},
	getDataById: function(idname, idvalue){
		for (var i = 0; i < treeTool.datas.length; i += 1) {
			if (parseInt(treeTool.datas[i][idname]) == parseInt(idvalue)){
				return treeTool.datas[i]
			}
		}
	},
	showTips: function(tipNames, tipSize, idname, contentHandler){
		$(tipNames).tooltip({
			content: $('<div></div>'),
			showEvent: 'click',
			position: 'right',
			onUpdate: function(content){
				var data = treeTool.getDataById(idname,($(this)).context.id);
				content.panel({
					width: tipSize,
					border: false,
					content:$('<div><pre>'+contentHandler(data)+'</pre></div>')
				});
			}, onShow: function(){
				t = $(this);
				t.tooltip('tip').unbind().bind('mouseleave', function(){
					t.tooltip('hide');
				});
			}
		});
	},
	getLoadDataJson: function(dataCols, datas,pageSize){
		return {
			columns : [ dataCols ],
			data : datas,
			pageSize: pageSize,
			loadFilter : function(data) {
				if (typeof data.length == 'number'
						&& typeof data.splice == 'function') {
					data = {
						total : data.length,
						rows : data
					}
				}
				var dg = $(this);
				var opts = dg.datagrid('options');
				var pager = dg.datagrid('getPager');
				pager.pagination({
					onSelectPage : function(pageNum, pageSize) {
						opts.pageNumber = pageNum;
						opts.pageSize = pageSize;
						pager.pagination('refresh', {
							pageNumber : pageNum,
							pageSize : pageSize
						});
						dg.datagrid('loadData', data);
					}
				});
				if (!data.originalRows) {
					data.originalRows = (data.rows);
				}
				var start = (opts.pageNumber - 1)
						* parseInt(opts.pageSize);
				var end = start + parseInt(opts.pageSize);
				data.rows = (data.originalRows.slice(start, end));
				return data;
			}
		}
	}
}

$.extend($.fn.datagrid.methods, {
	editCell: function(jq,param){
		return jq.each(function(){
			var opts = $(this).datagrid('options');
			var fields = $(this).datagrid('getColumnFields',true).concat($(this).datagrid('getColumnFields'));
			for(var i=0; i<fields.length; i++){
				var col = $(this).datagrid('getColumnOption', fields[i]);
				col.editor1 = col.editor;
				if (fields[i] != param.field){
					col.editor = null;
				}
			}
			$(this).datagrid('beginEdit', param.index);
			for(var i=0; i<fields.length; i++){
				var col = $(this).datagrid('getColumnOption', fields[i]);
				col.editor = col.editor1;
			}
		});
	}
});

$.fn.combobox.defaults.filter = function (q,row){
	var opts=$(this).combobox("options");
	try{
		return row[opts.textField].toLowerCase().indexOf(q.toLowerCase())>=0 ||(row.info&& row.info.toLowerCase().indexOf(q.toLowerCase())>=0);
	}catch(e){
		return false;
	}
}

$.fn.combobox.defaults.formatter = function (row){
	var opts=$(this).combobox("options");
	return row[opts.textField] +(row.info?(" "+row.info):"");
}
