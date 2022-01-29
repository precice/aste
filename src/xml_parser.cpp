#include "xml_parser.hpp"

namespace aste {

std::shared_ptr<tinyxml2::XMLDocument> loadXML(const std::string &fName)
{
  std::shared_ptr<tinyxml2::XMLDocument> xmlDoc = std::make_shared<tinyxml2::XMLDocument>();
  xmlDoc->LoadFile(fName.c_str());
  return xmlDoc;
}

tinyxml2::XMLElement *getRootElement(std::shared_ptr<tinyxml2::XMLDocument> xmlDoc)
{
  tinyxml2::XMLElement *pRootElement = xmlDoc->RootElement();
  return pRootElement;
}

int getDimension(tinyxml2::XMLElement *rootElement)
{
  auto solverInterface = rootElement->FirstChildElement("solver-interface");
  return std::stoi(solverInterface->Attribute("dimensions"));
}

std::vector<std::string> getScalarDatanames(tinyxml2::XMLElement *rootElement)
{
  std::vector<std::string> datanames;
  auto                     solverInterface = rootElement->FirstChildElement("solver-interface");
  auto                     scalardata      = solverInterface->FirstChildElement("data:scalar");
  while (scalardata != NULL) {
    std::string dataname;
    dataname.assign(scalardata->Attribute("name"));
    datanames.push_back(dataname);
    scalardata = scalardata->NextSiblingElement("data:scalar");
  }
  return datanames;
}

std::vector<std::string> getVectorDatanames(tinyxml2::XMLElement *rootElement)
{
  std::vector<std::string> vectorDatanames;
  auto                     solverInterface = rootElement->FirstChildElement("solver-interface");
  auto                     vectordata      = solverInterface->FirstChildElement("data:vector");
  while (vectordata != NULL) {
    std::string dataname;
    dataname.assign(vectordata->Attribute("name"));
    vectorDatanames.push_back(dataname);
    vectordata = vectordata->NextSiblingElement("data:vector");
  }
  return vectorDatanames;
}

std::vector<std::string> getWriteDatanames(tinyxml2::XMLElement *rootElement, const std::string &participant)
{
  std::vector<std::string> writeDatanames;
  auto                     solverInterface    = rootElement->FirstChildElement("solver-interface");
  auto                     participantElement = solverInterface->FirstChildElement("participant");
  auto                     participantName    = participantElement->Attribute("name");
  while (std::string(participantName) != participant && participantElement != NULL) {
    participantElement = participantElement->NextSiblingElement("participant");
    participantName    = participantElement->Attribute("name");
  }

  auto writedata = participantElement->FirstChildElement("write-data");
  while (writedata != NULL) {
    writeDatanames.push_back(std::string(writedata->Attribute("name")));
    writedata = writedata->NextSiblingElement("write-data");
  }
  return writeDatanames;
}

std::vector<std::string> getReadDatanames(tinyxml2::XMLElement *rootElement, const std::string &participant)
{
  std::vector<std::string> readDatanames;
  auto                     solverInterface    = rootElement->FirstChildElement("solver-interface");
  auto                     participantElement = solverInterface->FirstChildElement("participant");
  auto                     participantName    = participantElement->Attribute("name");
  while (std::string(participantName) != participant && participantElement != NULL) {
    participantElement = participantElement->NextSiblingElement("participant");
    participantName    = participantElement->Attribute("name");
  }

  auto writedata = participantElement->FirstChildElement("read-data");
  while (writedata != NULL) {
    readDatanames.push_back(std::string(writedata->Attribute("name")));
    writedata = writedata->NextSiblingElement("read-data");
  }
  return readDatanames;
}

std::string getMeshName(tinyxml2::XMLElement *rootElement, const std::string &participant)
{
  std::string meshname;
  auto        solverInterface    = rootElement->FirstChildElement("solver-interface");
  auto        participantElement = solverInterface->FirstChildElement("participant");
  auto        participantName    = participantElement->Attribute("name");
  while (std::string(participantName) != participant && participantElement != NULL) {
    participantElement = participantElement->NextSiblingElement("participant");
    participantName    = participantElement->Attribute("name");
  }

  auto meshdata = participantElement->FirstChildElement("use-mesh");
  bool provided{false};
  while (meshdata != NULL && !provided) {
    provided = (std::string(meshdata->Attribute("provide")) == "yes");
    if (provided) {
      meshname = std::string(meshdata->Attribute("name"));
    }
    meshdata = meshdata->NextSiblingElement("use-mesh");
  }
  return meshname;
}
} // namespace aste