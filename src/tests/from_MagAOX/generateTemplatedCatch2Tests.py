#!/bin/env python3

'''
Generate Catch2 tests from template.
See README.md for more details.
'''

import os
import sys
import subprocess
import glob
import re
import pathlib
import string
import random

# check jinja2 is installed. install it if not
try:
    import jinja2
except ModuleNotFoundError:
    print("module 'Jinja2' is not installed. Installing Jinja2...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'Jinja2'])
    import jinja2


'''
Get base type of log. This is needed for log types that inherit from a base type
that specfies the messageT(...)
'''
def getBaseType(lines : list) -> str:
    # use regex to find #include "<baseType>.hpp"
    baseType = ""
    for line in lines:
        match = re.search(r'^#include "[a-z_]*\.hpp"$', line)
        if match != None:
            baseType = line.strip().split()
            baseType = line.strip().split('"')[1].split(".")[0]
    return baseType


'''
NOTE: This relies on name order in .fbs schema and .hpp files to be the same.
'''
def getSchemaFieldInfo(fname : str) -> tuple[str, tuple] :
    schemaFolderPath = "./types/schemas/"
    schemaFolderPath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), schemaFolderPath)
    )

    schemaFilePath = os.path.join(schemaFolderPath, f"{fname}.fbs")
    if not os.path.isfile(schemaFilePath):
        return "", tuple()

    schemaFile = open(schemaFilePath, "r")

    schemaFieldInfo = []
    subTables = dict() # dict where key is sub-table name, value is [(fieldname, type)...]
    curSubTable = None
    inTable = False
    schemaTableName = ""
    for line in schemaFile:
        if "table" in line:
            # check if `table <log_type>_fb`
            match = re.search(r'^table [a-zA-Z_]*_fb', line)
            if match != None:
                line = line.strip().split()
                tableIdx = line.index("table")
                schemaTableName =  line[tableIdx + 1]
            # otherwise it is a sub-table
            else:
                line = line.strip().split()
                subNameIdx = line.index("table")
                subName =  line[subNameIdx + 1]
                subTables[subName] = []
                curSubTable = subName # we are in a sub-table of the schema

        if not inTable and "{" in line:
            inTable = True
            continue

        if inTable:
            line = line.strip()
            if ("//" in line):
                continue

            if ("}" in line):
                inTable = False
                curSubTable = None
                continue

            if (line != ""):
                lineParts = line.strip().rstrip(";").split(":")
                name = lineParts[0]
                type = lineParts[1].split()[0]

                if curSubTable is not None:
                    # add to subtable dict for now, will be added in later
                    subTables[curSubTable].append((name, type))
                else:
                    schemaFieldInfo.append((name, type))
                continue

    if len(subTables) == 0:
        return schemaTableName, tuple(schemaFieldInfo)
    

    # go through sub tables and add them in
    newSchemaFieldInfo = []
    for field in schemaFieldInfo:
        fieldType = field[1]
        if fieldType in subTables.keys():
               newSchemaFieldInfo.append({field[0] : subTables[fieldType]})
        else:
            newSchemaFieldInfo.append(field)
    # print(newSchemaFieldInfo)
    return schemaTableName, tuple(newSchemaFieldInfo)


'''
Quick check that the types in .fbs correspond, mainly strings match to strings, 
and vectors to vectors.
If they do not correspond, the behavior for comparing the fb values in the tests
is undefined, and action beyond this generator will need to be taken.
'''
def typesCorrespond(fbsType : str, cType : str) -> bool:
    if ("[" in fbsType) or ("vector" in cType):
        return ("[" in fbsType) and ("vector" in cType)

    if ("string" in fbsType) or ("string" in cType or "char *" in cType):
        return (("string" in fbsType) and ("string" in cType or "char *" in cType))
    
    return True
    

'''
Check it is not a base log type.
Must have eventCode and defaultLevel
'''
def isValidLogType(lines : list) -> bool:
    hasEventCode = False
    hasDefaultLevel = False
    for line in lines:

        # check event code
        eventCode = re.search("flatlogs::eventCodeT eventCode = eventCodes::[A-Za-z_0-9]*;", line)
        if eventCode != None:
            hasEventCode = True

        # check default level
        defaultLevel = re.search("flatlogs::logPrioT defaultLevel = flatlogs::logPrio::[A-Za-z_0-9]*;", line)
        if defaultLevel != None:
            hasDefaultLevel = True

        # if we have both already, return
        if hasEventCode and hasDefaultLevel:
            return True

    return (hasEventCode and hasDefaultLevel)



def makeTestInfoDict(hppFname : str, baseTypesDict : dict) -> dict:
    returnInfo = dict()
    headerFile = open(hppFname,"r")

    # add name of test/file/type to be generated
    fNameParts = hppFname.split("/")
    returnInfo["name"] = fNameParts[-1].strip().split(".")[0]
    print(f"LOGNAME: {returnInfo["name"]}")
    returnInfo["genTestFname"] = f"{returnInfo['name']}_generated_tests.cpp"
    returnInfo["className"] = "C" + "".join([word.capitalize() for word in returnInfo["name"].split("_")])
    returnInfo["classVarName"] = "".join([word[0].lower() for word in returnInfo["name"].split("_")])
    returnInfo["baseType"] = "flatbuffer_log" # the default
    returnInfo["hasGeneratedHfile"] = hasGeneratedHFile(returnInfo["name"])

    headerLines = headerFile.readlines()

    # cannot generate tests from this file alone, need base type
    if not isValidLogType(headerLines):
        if returnInfo["name"] not in baseTypesDict:
            baseTypesDict[returnInfo["name"]] = set()
        return None # don't render anything from this file

    # find where messageT structs are being made -> describes fields
    messageStructIdxs = []
    for i in range(len(headerLines)):
        if "messageT(" in headerLines[i]:
            messageStructIdxs.append(i)

    schemaTableName, schemaFieldInfo = getSchemaFieldInfo(returnInfo["name"])
    returnInfo["schemaTableName"] = schemaTableName

    # handle log types that inherit from base types
    if len(messageStructIdxs) == 0:
        # get base type
        baseType = getBaseType(headerLines)

        if baseType not in baseTypesDict:
            baseTypesDict[baseType] = set()

        # add inhertied type to dict where val is the base type it inherits from
        baseTypesDict[baseType].add(returnInfo["name"])
        return None # don't render me yet!


    returnInfo["messageTypes"], error = getMessageFieldInfo(messageStructIdxs, headerLines, schemaFieldInfo)
    if error:
        return None # error, don't render
    
    return returnInfo

'''
Parse out field type and name from string
'''
def getTypeAndName(lineParts : list) -> tuple[str, str]:

    typeIdxStart = 1 if (lineParts[0] == "const") else 0
    type = lineParts[typeIdxStart]

    if lineParts[typeIdxStart + 1] == "&":
        nameIdx = (typeIdxStart + 2)
    elif lineParts[typeIdxStart + 1] == "*":
        nameIdx = (typeIdxStart + 2)
        type += " " + lineParts[typeIdxStart + 1]
    else:
        nameIdx = (typeIdxStart + 1)

    name = lineParts[nameIdx].rstrip(")").rstrip(",")

    return type, name

'''
Checks if log type has a corresponding generated .h file in ./types/generated
'''
def hasGeneratedHFile(logName : str) -> bool:
    generatedFolderPath = "./types/generated/"
    generatedFolderPath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), generatedFolderPath)
    )

    generatedFilePath = os.path.join(generatedFolderPath, f"{logName}_generated.h")
    if os.path.isfile(generatedFilePath):
        return True

    return False

def getRandInt(type : str) -> int:
    unsigned = True if "uint" in type else False

    sizeBits = 8 # default size 8 bits
    if "_t" in type:
        typeParts = type.split("_t")
        if int(typeParts[0][-1]) != 8:
            sizeBits = int(typeParts[0][-2])
    
    if not unsigned:
        sizeBits -= 1

    max = (2 ** sizeBits) - 1
    min = 0 if unsigned else (0 - max - 1)

    return random.randint(min, max)

def getRandValFromType(fieldType : str, schemaFieldType = None) -> str:
    if "bool" in fieldType or (schemaFieldType is not None and "bool" in schemaFieldType):
        return "1"
    elif "string" in fieldType or "char *" in fieldType:
        randString = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        return f'"{randString}"'
    elif "int" in fieldType:
        return str(getRandInt(fieldType))
    elif "float" in fieldType:
        return str(round(random.random(), 6))
    elif "double" in fieldType:
        return str(round(random.random(), 14))
    else:
        return "{}"


def makeTestVal(fieldDict : dict) -> str:
    if "vector" in fieldDict["type"]:
        vals = [ getRandValFromType(fieldDict["vectorType"]) for i in range(10)]
        return f"{{ {",".join(vals)} }}"

    if "schemaType" in fieldDict:
        return getRandValFromType(fieldDict["type"], fieldDict["schemaType"])
    
    return getRandValFromType(fieldDict["type"])
    


'''
make 2d array. each inner array contains dictionaries corresponding to
the type(s) and name(s) of field(s) in a message:
[ [ {type : x, name: y ...}, {name: type, ...} ], ... ]
'''
def getMessageFieldInfo(messageStructIdxs: list, lines : list, schemaFieldInfo : tuple):
    msgTypesList = []
    error = False
    subTableDictIndex = 0

    # extract log field types and names
    for i in range(len(messageStructIdxs)):
        structIdx = messageStructIdxs[i]
        msgsFieldsList = []

        closed = False
        fieldCount = 0
        while not closed and structIdx < len(lines):

            line = lines[structIdx]

            # check if this is a closing line
            if ")" in line:
                if "//" in line and line.find(")") > line.find("//"):
                    # parenthesis is in comment
                    pass
                elif line.strip().strip(")") == "":
                    break
                else:
                    closed = True # parse the field, don't leave loop yet


            # trim line to just get field info
            indexStart = (line.find("messageT(") + len("messageT(")) if "messageT(" in line else 0
            indexEnd = line.find("//") if "//" in line else len(line)
            line = line[indexStart:indexEnd]

            lineParts =  [part.strip().split() for part in line.strip().rstrip(",").split(",")]

            for field in lineParts:
                fieldDict = {}
                if len(field) > 0 and "//" in field[0]:
                    break

                # find type and name
                type, name = getTypeAndName(field)

                fieldDict["type"] = type
                fieldDict["name"] = name
                # get vector type if necessary
                if "std::vector" in fieldDict["type"]:
                    typeParts = fieldDict["type"].split("<")
                    vectorIdx = [i for i, e in enumerate(typeParts) if "std::vector" in e][0]
                    vectorType = typeParts[vectorIdx + 1].strip(">")
                    fieldDict["vectorType"] = vectorType

                if len(schemaFieldInfo) != 0:
                    if isinstance(schemaFieldInfo[fieldCount], tuple):
                        fieldDict["schemaName"] = schemaFieldInfo[fieldCount][0]
                        fieldDict["schemaType"] = schemaFieldInfo[fieldCount][1]
                        fieldCount += 1
                    else:
                        # go into dictionary..
                        subTableName = next(iter(schemaFieldInfo[fieldCount]))
                        schemaFieldName = schemaFieldInfo[fieldCount][subTableName][subTableDictIndex][0]
                        schemaFieldType = schemaFieldInfo[fieldCount][subTableName][subTableDictIndex][1]
                        fieldDict["schemaName"] = f"{subTableName}()->{schemaFieldName}"
                        fieldDict["schemaType"] = schemaFieldType
                        subTableDictIndex += 1
                        if (subTableDictIndex >= len(schemaFieldInfo[fieldCount][subTableName])):
                            # reset dictionary index if we need to
                            subTableDictIndex = 0
                            fieldCount += 1
                    
                    # check schemaType correlates to type in .hpp file
                    if not typesCorrespond(fieldDict["schemaType"], fieldDict["type"]):
                        print(f"  ERROR undefined behavior: types for field '{fieldDict["name"]}' do not correlate.")
                        print(f"    schemaType: {fieldDict["schemaType"]}, type: {fieldDict["type"]}")
                        error = True
                
                fieldDict["testVal"] = makeTestVal(fieldDict)

                # add field dict to list of fields
                msgsFieldsList.append(fieldDict)

            structIdx += 1
            
        # if fieldCount != len(schemaFieldInfo):
        #     # don't add cases where field count != schema field count
        #     # only an issue for software_log, not an issue for telem_stdcam
        #     # print(f"fieldCount={fieldCount} len(schemaFieldInfo)={len(schemaFieldInfo)}")
        #     # print("HERE")
        #     continue
        msgTypesList.append(msgsFieldsList)

    return msgTypesList, error

def makeInheritedTypeInfoDict(typesFolderPath : str, baseName : str, logName : str) -> dict:
    returnInfo = dict()

    baseFilePath = os.path.join(typesFolderPath, f"{baseName}.hpp")
    baseHFile = open(baseFilePath,"r")

    # add name of test/file/type to be generated
    print(f"LOGNAME: {logName}")
    returnInfo["name"] = logName
    returnInfo["genTestFname"] = f"{returnInfo['name']}_generated_tests.cpp"
    returnInfo["className"] = "".join([word[0].upper() for word in returnInfo["name"].split("_")]) + "_Class"
    returnInfo["classVarName"] = returnInfo["className"].split("_")[0].lower()
    returnInfo["baseType"] = baseName
    returnInfo["hasGeneratedHfile"] = hasGeneratedHFile(logName)


    baseHLines = baseHFile.readlines()

    # find where messageT structs are being made in base log file -> describes fields
    messageStructIdxs = []
    for i in range(len(baseHLines)):
        if "messageT(" in baseHLines[i]:
            messageStructIdxs.append(i)

    schemaTableName, schemaFieldInfo = getSchemaFieldInfo(baseName)

    returnInfo["schemaTableName"] = schemaTableName
    msgFieldInfo, error = getMessageFieldInfo(messageStructIdxs, baseHLines, schemaFieldInfo)
    if error:
        return None # error, don't render
    
    returnInfo["messageTypes"] = [[]] if "empty_log" in baseName else msgFieldInfo

    return returnInfo

def versionAsNumber(major, minor):
    return (major * 1000 + minor)

def main():
    # check python version >= 3.9
    if (versionAsNumber(sys.version_info[0], sys.version_info[1]) < versionAsNumber(3,9)):
        print("Error: Python version must be >= 3.9")
        exit(0)

    # load template
    env = jinja2.Environment(
        loader = jinja2.FileSystemLoader(searchpath="./")
    )
    env.trim_blocks = True
    env.lstrip_blocks = True
    catchTemplate = env.get_template("catch2TestTemplate.jinja2")

    # path to .hpp files here
    typesFolderPath = "./types"
    typesFolderPath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), typesFolderPath)
    )

    # generated tests output path
    generatedTestsFolderPath = "./generated_tests/"
    generatedTestsFolderPath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), generatedTestsFolderPath)
    )

    # make directory if it doesn't exist
    pathlib.Path(generatedTestsFolderPath).mkdir(exist_ok=True)
    oldFiles = glob.glob(os.path.join(generatedTestsFolderPath, "*"))
    for file in oldFiles:
        os.remove(file)

    types = os.listdir(typesFolderPath)
    types.sort()
    baseTypesDict = dict() # map baseTypes to the types that inherit from them
    for type in types:

        # check valid type to generate tests for
        if ".hpp" not in type:
            continue

        typePath = os.path.join(typesFolderPath, type)

        # make dictionary with info for template
        info = makeTestInfoDict(typePath, baseTypesDict)
        if (info is None):
            # empty dictionary, no tests to make
            continue

        # render
        renderedHeader = catchTemplate.render(info)

        # write generated file
        outPath = os.path.join(generatedTestsFolderPath, info["genTestFname"])
        with open(outPath,"w") as outfile:
            print(renderedHeader,file=outfile)

    # handle types that inherit from baseTypes
    for baseType, inheritedTypes in baseTypesDict.items():

        if len(inheritedTypes) == 0:
            continue

        for inheritedType in inheritedTypes:
            info = makeInheritedTypeInfoDict(typesFolderPath, baseType, inheritedType)
            if (info is None):
                # empty dictionary, no tests to make
                continue

            # render
            renderedHeader = catchTemplate.render(info)

            # write generated file
            outPath = os.path.join(generatedTestsFolderPath, info["genTestFname"])
            with open(outPath,"w") as outfile:
                print(renderedHeader,file=outfile)


if (__name__ == "__main__"):
    main()