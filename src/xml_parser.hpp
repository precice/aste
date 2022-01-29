#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include "tinyxml2.h"

namespace aste {

std::shared_ptr<tinyxml2::XMLDocument> loadXML(const std::string &fName);

tinyxml2::XMLElement *getRootElement(std::shared_ptr<tinyxml2::XMLDocument> xmlDoc);

int getDimension(tinyxml2::XMLElement *rootElement);

std::vector<std::string> getScalarDatanames(tinyxml2::XMLElement *rootElement);

std::vector<std::string> getVectorDatanames(tinyxml2::XMLElement *rootElement);

std::vector<std::string> getWriteDatanames(tinyxml2::XMLElement *rootElement, const std::string &participant);

std::vector<std::string> getReadDatanames(tinyxml2::XMLElement *rootElement, const std::string &participant);

std::string getMeshName(tinyxml2::XMLElement *rootElement, const std::string &participant);

} // namespace aste