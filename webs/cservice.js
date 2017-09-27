DataOperation = {
	IsObject: function(tempVal){
		return '[object Object]' == Object.prototype.toString.call(tempVal);
	},
	IsArray: function(tempVal){
		return '[object Array]' == Object.prototype.toString.call(tempVal);
	},
	IsString: function(tempVal){
		return '[object String]' == Object.prototype.toString.call(tempVal);
	},
	IsNumber: function(tempVal){
		return '[object Number]' == Object.prototype.toString.call(tempVal);
	},
	IsBoolean: function(tempVal){
		return '[object Boolean]' == Object.prototype.toString.call(tempVal);
	},
	JsonToArray: function(jsonobj){
		var jarray = []
		for(var k in jsonobj){
			var jele = {'key':k}
			jarray.push(jele)
			var v = jsonobj[k]
			if(DataOperation.IsObject(v)){
				for(var kk in v)
					jele['.'+kk] = v[kk]
			}else
				jele['val'] = v
		}
		return jarray
	},
	JsonToString: function(jsonObj, lineEnd, lineStr, isPureString){

		if(jsonObj==null || undefined==jsonObj)
			return "null"

		if(undefined == lineStr)
			lineStr = "  "
		if(undefined == isPureString)
			isPureString = true
		if(undefined == lineEnd)
			lineEnd = "\n"

		if(DataOperation.IsString(jsonObj)){
			return isPureString?jsonObj:('"' + jsonObj.replace(/"/g,'\\"').replace(/\n/g, "\\n") + '"')
		}
		if(DataOperation.IsNumber(jsonObj) || DataOperation.IsBoolean(jsonObj)){
			return "" + jsonObj
		}

		if(JSON && JSON.stringify){
			return JSON.stringify(jsonObj)
		}

		var isArray = DataOperation.IsArray(jsonObj)
		var jsonStr = ""
		if(isArray)
			for(var objIndex in jsonObj){
				if(jsonStr!="")
					jsonStr += ", "
				jsonStr += DataOperation.JsonToString(jsonObj[objIndex], lineEnd, lineStr + lineStr, false)
			}
		else
			for(var objIndex in jsonObj){
				if(jsonStr!="")
					jsonStr += ", " + lineEnd
				jsonStr += lineStr + '"' + objIndex + '": ' + DataOperation.JsonToString(jsonObj[objIndex], lineEnd, lineStr + lineStr,false)
			}
		return isArray?("["+jsonStr+"]"):("{"+jsonStr+"}")
	},
	GetCondition:function(condStr){
		if(condStr==undefined){
			var curHref =  window.location.href
			if(curHref.endsWith("#"))
			   curHref = curHref.substring(0,curHref.length-1)
			condStr = decodeURIComponent(curHref)
		}
		var jcond={}
		try{
			var conds;
			if(condStr.indexOf("#")>0)
				conds = condStr.substr(condStr.indexOf("#")+1).split('&')
			else
				conds = condStr.substr(condStr.indexOf("?")+1).split('&')
			for(var condIndex in conds){
				var cnIndex = conds[condIndex].indexOf("=")
				jcond[conds[condIndex].substr(0,cnIndex)]=conds[condIndex].substr(cnIndex+1)
			}
			return jcond
		}catch(e){return jcond}
	},
	GetSortKey: function(jsonObj){
		var objKeys = []
		for(var kn in jsonObj)
			objKeys = objKeys.concat(kn)
		objKeys.sort()
		return objKeys
	}
}

HtmlTag ={
	'GetDay': function(refDay, dayNum){
		nowDay = new Date(refDay)
		tDay = new Date(nowDay.getTime()-86400*1000*(nowDay.getDay()-dayNum))
		return ""+tDay.getFullYear() + "-" + (tDay.getMonth()+1) + "-" + tDay.getDate()
	},
	'GetObj': function(objName, objIndex){
		nameObj = document.getElementsByName(objName)
		if(nameObj.length==0)
			return document.getElementById(objName)
		return nameObj[objIndex==null? nameObj.length-1 :objIndex]
	},
	'SetVal': function(valName, val, valIndex, attName){
		HtmlTag.GetObj(valName,valIndex)[attName==null?"value":attName] = val==null?"": ( attName=='innerHTML'? val.toString().replace(/\\n/g,"<br>"):val.toString().replace(/\r/g,"\\r") )
	},
	'GetVal': function(valName, valIndex, attName){
		return HtmlTag.GetObj(valName,valIndex)[attName==null?"value":attName]
	},
	'AddOption': function(selName, optName, optVal, objIndex){
		var opt = new Option(optName,optVal)
		opt.innerHTML = optName
		HtmlTag.GetObj(selName,objIndex).appendChild(opt)
	},
	'RemoveChildren': function(objName, leftChildren){
		var obj = HtmlTag.GetObj(objName)
		while(obj.children.length > leftChildren)
			obj.remove(obj.children[obj.children.length])
	},
	'AppendElement': function(parentEle, tagName, typeAttr, nameAttr, valueAttr, htmlText, attName, attValue){
		var tEle = document.createElement(tagName)
		if(typeAttr != undefined)
			tEle.setAttribute("type", typeAttr)
		
		if(nameAttr != undefined)
			tEle.setAttribute("name", nameAttr)

		if(valueAttr != undefined)
			tEle.setAttribute("value", valueAttr)

		if(attName != undefined)
			tEle.setAttribute(attName, attValue)

		if(htmlText != undefined)
			tEle.innerHTML = htmlText

		if(parentEle != undefined)
			parentEle.appendChild(tEle)
		return tEle
	},
	'KeyEvent': function(actKey, expKey, eHandleStr){
		if(actKey == expKey){
			return eval(eHandleStr)
		}
	},
	'SetTriggerVal' : function(objNames, propLocator, val1, val2, fromIndex, toIndex){
		if(toIndex==null){
			props = propLocator.split('.')
			objNameArray = objNames.split(',')
			for(objNameIndex in objNameArray){
				objName=objNameArray[objNameIndex]
				tobj = HtmlTag.GetObj(objName , fromIndex)
				for(pIndex in props){
					if(pIndex < props.length-1){
						tobj = tobj[props[pIndex]]
					}
				}
				if(tobj[props[pIndex]] == val1){
					tobj[props[pIndex]] = val2
				}else{
					tobj[props[pIndex]] = val1
				}
			}
		}else{
			while(fromIndex <= toIndex){
				HtmlTag.SetTriggerVal(objNames, propLocator, val1, val2, fromIndex)
				fromIndex += 1
			}
		}
	},
	'GetByJsonLocator' : function (tArrayJson, matchKey, matchVal, retKey, defVal){
		for(index in tArrayJson){
			if(matchVal == tArrayJson[index][matchKey]){
				if(retKey==null)
					return tArrayJson[index]
				return tArrayJson[index][retKey]
			}
		}
		return defVal==undefined?matchVal:defVal
	},
	'GetComplexVal' : function (name, isGetValue){
		var cobjs = document.getElementsByName(name)

		var retVal = ""
		for( var objIndex=0; objIndex< cobjs.length; objIndex++){
			obj = cobjs[objIndex]
			if(obj.type == "checkbox" || obj.type == "radio"){
				if(isGetValue==true || obj.checked){
					retVal += (retVal==""?"":",") + obj.value
				}
			}else
				retVal += (retVal==""?"":",") + obj.value
		}
		return retVal
	},
	'SetComplexVal' : function (name, value, isKeepValue){
		var cobjs = document.getElementsByName(name)

		for( var objIndex=0; objIndex< cobjs.length; objIndex++){
			obj = cobjs[objIndex]
			if(obj.type == "checkbox" || obj.type == "radio"){
				if(obj.value == value)
					obj.checked = true
				else if(!(true == isKeepValue))
					obj.checked = false
			}
		}
	},
	'GetTableObj': function(obj, objName){
		if(undefined == objName)
			objName = 'TABLE'
		while(obj.tagName!='BODY'){
			if(obj.tagName==objName)
				return obj
			obj = obj.parentNode
		}
	},
	CloneTableObj: function(objName, giveId, parentTag){
		var tbObj = HtmlTag.GetObj(objName)
		var parentObj = HtmlTag.GetTableObj(tbObj, parentTag)
		tbObj = tbObj.cloneNode(true)
		tbObj.style.display = ""
		tbObj.id = giveId
		parentObj.appendChild(tbObj)
		return tbObj
	},
	DeleteTableObj: function(obj, parentTag){
		var parentObj = HtmlTag.GetTableObj(obj, parentTag)
		parentObj.removeChild(obj)
	},
	DeleteTableObjs: function (objName, keepIndex){
		var parentObj = HtmlTag.GetObj(objName)
		while(parentObj.childNodes.length > keepIndex){
			parentObj.removeChild(parentObj.childNodes[keepIndex])
		}
	},
	RenderSelect: function(objName, opNameVals, defValue, leftCount){
		if(undefined == leftCount){
			leftCount =0
		}
		HtmlTag.RemoveChildren(objName, leftCount)
		for(var opIndex in opNameVals){
			var op = opNameVals[opIndex]
			if(DataOperation.IsArray(op))
				HtmlTag.AddOption(objName, op[0], op.length>1?op[1]:op[0])
			else
				HtmlTag.AddOption(objName, op, op)
		}
		if(undefined != defValue){
			HtmlTag.SetVal(objName, defValue)
		}
	}
}
None = null
True = true
False = false
isAlertError = true
function cerviceRequest(apiPath, argNames, argVals, method) {

	var argLen = argNames.length;
	var jsonParam = {};
	for (argIndex = 0; argIndex < argLen; ) {
		if(undefined != argVals[argIndex]){
			jsonParam[argNames[argIndex]] = argVals[argIndex];
		}
		argIndex += 1;
	}

	var http = new XMLHttpRequest();

	http.open("POST", apiPath, false);
	http.send(DataOperation.JsonToString(jsonParam));

	try{
		var ctestResp = $.parseJSON(http.responseText)	
	}catch(e){
		if(e instanceof ReferenceError)
			try{
				return eval("ctestResp=" + http.responseText)
			}catch(e){}
		return http.responseText
	}
	if(ctestResp == null || undefined == ctestResp[0])
		return ctestResp
	if(ctestResp[0] != 0){
		if(isAlertError)
			alert(ctestResp[1])
		throw new Error(ctestResp[1])
	}
	return ctestResp[1];
}

datetime = new Object()
datetime.datetime = function(y,m,d,H,M){
	return y + "-" + (m<10?("0"+m):m )+ "-" + (d<10?("0"+d):d )
}

var myformatter = function(date){
	var y = date.getFullYear();
	var m = date.getMonth()+1;
	var d = date.getDate();
	return y + "-" + (m<10?("0"+m):m )+ "-" + (d<10?("0"+d):d )
}

var myparser = function(s){
	var t = Date.parse(s);
	if (!isNaN(t)){
		return new Date(t);
	} else {
		return new Date();
	}
}

