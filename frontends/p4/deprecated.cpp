/*
Copyright 2017 VMware, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

#include "frontends/common/resolveReferences/resolveReferences.h"
#include "deprecated.h"

namespace P4 {

class CheckGetMember : public Inspector {
    const ReferenceMap* refMap;
public:
    explicit CheckGetMember(const ReferenceMap* refMap): refMap(refMap)
    { CHECK_NULL(refMap); setName("CheckGetMember"); }

//    void warnIfGetMember(const IR::IAnnotated* declaration, const IR::Node* errorNode) {};

    bool preorder(const IR::PathExpression* path) override {std::cout << "path = " << path << std::endl;};
    bool preorder(const IR::Type_Name* name) override {std::cout << "name = " << name << std::endl;};
    bool preorder(const IR::P4Action* action) override {std::cout << "action = " << action << std::endl;};
};

void CheckDeprecated::warnIfDeprecated(
    const IR::IAnnotated* annotated, const IR::Node* errorNode) {
    if (annotated == nullptr)
        return;
    auto anno =
        annotated->getAnnotations()->getSingle(IR::Annotation::deprecatedAnnotation);
    if (anno == nullptr)
        return;

    cstring message = "";
    for (auto a : anno->expr) {
        if (auto str = a->to<IR::StringLiteral>())
            message += str->value;
    }
    ::warning(ErrorType::WARN_DEPRECATED, "%1%: Using deprecated feature %2%. %3%",
              errorNode, annotated->getNode(), message);
}

bool CheckDeprecated::preorder(const IR::P4Action* action) {
    std::cout << "Action name = " << action->getName() << std::endl;
    std::cout << "Action body = " << action->body << std::endl;
    for (int i = 0; i < action->body->components.size(); i++) { 
        std::cout << "Action action->body->components[i]->getNode()->node_type_name() = " << action->body->components[i]->getNode()->node_type_name() << std::endl;
        if (action->body->components[i]->getNode()->node_type_name() == "BlockStatement") {
            std::cout << "action->body->components[i] = " << action->body->components[i] << std::endl;
            std::cout << "Start processing " << std::endl;
            CheckGetMember chgm(this->refMap); 
            action->body->components[i]->getNode()->apply(chgm);
            std::cout << std::endl;
        }
    }
    return true;
}

bool CheckDeprecated::preorder(const IR::PathExpression* expression) {
    auto decl = refMap->getDeclaration(expression->path);
    CHECK_NULL(decl);
    warnIfDeprecated(decl->to<IR::IAnnotated>(), expression);
    return false;
}

bool CheckDeprecated::preorder(const IR::Type_Name* name) {
    auto decl = refMap->getDeclaration(name->path);
    CHECK_NULL(decl);
    warnIfDeprecated(decl->to<IR::IAnnotated>(), name);
    return false;
}

}  // namespace P4
