'''
 use jinja2 to generate catch tests

PRE_REQS:
 python >= 3.9
 jinja2

TODO:
- Maybe make a shell script to kick it off, check for install, install if not there,
  and then run the generator?
- In that script you could check the available version of python, and the library,
  and anything else you'll need.
- Add test generation to makefile

Questions:
- make vectors, ints have values - random
- no tests needed for base types?
    baseTypes = {"empty_log", "flatbuffer_log", "software_log", "string_log"}
    + saving_state_change, from what I can tell

don't plan on using, but don't want to delete again
# baseTypes = {"empty_log", "flatbuffer_log", "software_log", "string_log"}
# if [baseType for baseType in baseTypes if (baseType in type)] != []:
    #     continue

'''

import jinja2
import glob
import json
import os
import re
import pathlib

#!/bin/env python3

'''
Get base type of log. This is needed for log types that inherit from a base type
that specfies the messageT(...)
'''
def getBaseType(lines) -> str:

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
TODO: add this requirement to the README. There needs to be something to help
the generator in this situation. Alternatively, we could require
the fields be the same name as the fbs. but the former is probably better.
'''
def getSchemaFieldInfo(fname) -> tuple[str, tuple] :
    schemaFolderPath = "./types/schemas/"
    schemaFolderPath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), schemaFolderPath)
    )

    schemaFilePath = os.path.join(schemaFolderPath, f"{fname}.fbs")
    if not os.path.isfile(schemaFilePath):
        return "", tuple()

    schemaFile = open(schemaFilePath, "r")

    schemaFieldInfo = []
    inTable = False
    schemaTableName = ""
    for line in schemaFile:
        if "table" in line:
            line = line.strip().split(" ")
            tableIdx = line.index("table")
            schemaTableName =  line[tableIdx + 1]
        if not inTable and "{" in line:
            inTable = True
            continue

        if inTable:
            line = line.strip()
            if ("//" in line):
                continue

            if ("}" in line):
                inTable = False
                continue

            if (line != ""):
                lineParts = line.strip().rstrip(";").split(":")
                name = lineParts[0]
                type = lineParts[1]
                schemaFieldInfo.append((name, type))
                continue

    return schemaTableName, tuple(schemaFieldInfo)

'''
Very rudimentary way to check that the types in .fbs correspond
to the field cType (from.hpp file).
If not, the behavior for comparing the fb values in the tests is undefined,
and action beyond this generator will need to be taken.
'''
def typesCorrespond(fbsType, cType) -> bool:
    if ("[" in fbsType) or ("vector" in cType):
        return ("[" in fbsType) and ("vector" in cType)

    if ("string" in fbsType) or ("string" in cType or "char *" in cType):
        return (("string" in fbsType) and ("string" in cType or "char *" in cType))
    
    return True
    



'''
Check it is not a base log type.
Must have eventCode and defaultLevel
'''
def isValidLogType(lines) -> bool:
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


    returnInfo["messageTypes"] = getMessageFieldInfo(messageStructIdxs, headerLines, schemaFieldInfo)
    return returnInfo

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

'''
make 2d array. each inner array contains dictionaries corresponding to
the type(s) and name(s) of field(s) in a message:
[ [ {type : x, name: y ...}, {name: type, ...} ], ... ]
'''
def getMessageFieldInfo(messageStructIdxs: list, lines : list, schemaFieldInfo : tuple):
    msgTypesList = []

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

            lineParts =  [part.strip().split(" ") for part in line.strip().rstrip(",").split(",")]

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
                    fieldDict["schemaName"] = schemaFieldInfo[fieldCount][0]
                    fieldDict["schemaType"] = schemaFieldInfo[fieldCount][1]
                    # check schemaType correlates to type in .hpp file
                    if not typesCorrespond(fieldDict["schemaType"], fieldDict["type"]):
                        print(f"  ERROR undefined behavior: types for field {fieldDict["name"]} do not correlate.")
                        print(f"  schemaType: {fieldDict["schemaType"]}, type: {fieldDict["type"]}")
                    fieldCount += 1

                # add field dict to list of fields
                msgsFieldsList.append(fieldDict)

            structIdx += 1

        msgTypesList.append(msgsFieldsList)

    return msgTypesList

def makeInheritedTypeInfoDict(typesFolderPath : str, baseName : str, logName : str):
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
    returnInfo["messageTypes"] = [[]] if "empty_log" in baseName else \
                                getMessageFieldInfo(messageStructIdxs, baseHLines, schemaFieldInfo)

    return returnInfo



def main():
    # load template
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath="./")
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
        # print(f"deleting {file}")
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
