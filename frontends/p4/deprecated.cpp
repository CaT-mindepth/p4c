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

    bool preorder(const IR::PathExpression* path) override {std::cout << "PathExpression* path = " << path << std::endl; return true;};
    bool preorder(const IR::Type_Name* name) override {std::cout << "Type_Name* name = " << name << std::endl; return true; };
    bool preorder(const IR::P4Action* action) override {std::cout << "P4Action action = " << action << std::endl; return true;};
    bool preorder(const IR::Expression* expression) override {std::cout << "Expression* expression = " << expression << std::endl; return true;};
    bool preorder(const IR::P4Parser *p) override {std::cout << "P4Parser *p4parser = " << p << std::endl; return true;};
    bool preorder(const IR::ParserState *ps) override {std::cout << "ParserState *ps = " << ps << std::endl; return true;};
    bool preorder(const IR::P4ValueSet *pvs) override {std::cout << "P4ValueSet *pvs = " << pvs << std::endl; return true;};
    bool preorder(const IR::SelectExpression *se) override {std::cout << "SelectExpression *se = " << se << std::endl; return true;};
    bool preorder(const IR::SelectCase *sc) override {std::cout << "SelectCase *sc = " << sc << std::endl; return true;};
    bool preorder(const IR::P4Control *c) override {std::cout << "P4Control *c = " << c << std::endl; return true;};
    bool preorder(const IR::Type_Extern *t) override {std::cout << "Type_Extern *t = " << t << std::endl; return true;};
    bool preorder(const IR::Type_Method *t) override {std::cout << "Type_Method *t = " << t << std::endl; return true;};
    bool preorder(const IR::Method *method) override {std::cout << "Method *method = " << method << std::endl; return true;};
    bool preorder(const IR::Function *function) override {std::cout << "Function *function = " << function << std::endl; return true;};
    bool preorder(const IR::P4Table *p4table) override {std::cout << "P4Table *p4table = " << p4table << std::endl; return true;};
    bool preorder(const IR::Property *p) override {std::cout << "Property *p = " << p << std::endl; return true;};
    bool preorder(const IR::ActionList *acl) override {std::cout << "ActionList *acl = " << acl << std::endl; return true;};
    bool preorder(const IR::Entry *e) override {std::cout << "Entry *e = " << e << std::endl; return true;};
    bool preorder(const IR::EntriesList *el) override {std::cout << "EntriesList *el = " << el << std::endl; return true;};
    bool preorder(const IR::Key *key) override {std::cout << "Key *key = " << key << std::endl; return true;};
    bool preorder(const IR::KeyElement *ke) override {std::cout << "KeyElement *ke = " << ke << std::endl; return true;};
    bool preorder(const IR::ExpressionValue *ev) override {std::cout << "ExpressionValue *ev = " << ev << std::endl; return true;};
    bool preorder(const IR::MethodCallExpression *mce) override {
        std::cout << "MethodCallExpression *mce = " << mce << std::endl;
        std::cout << "MethodCallExpression *mce->method = " << mce->method << std::endl; return true;
    };
    bool preorder(const IR::ListExpression *le) override {std::cout << "ListExpression *le = " << le << std::endl; return true;};
    bool preorder(const IR::BlockStatement *b) override {std::cout << "BlockStatement *b = " << b << std::endl; return true;};
    bool preorder(const IR::EmptyStatement *emptystmt) override {std::cout << "EmptyStatement *emptystmt = " << emptystmt << std::endl; return true;};
    bool preorder(const IR::ExitStatement *exitstmt) override {std::cout << "ExitStatement *exitstmt = " << exitstmt << std::endl; return true;};
    bool preorder(const IR::ReturnStatement *r) override {std::cout << "ReturnStatement * = " << r << std::endl; return true;};
    bool preorder(const IR::AssignmentStatement *as) override {std::cout << "AssignmentStatement *as = " << as << std::endl; return true;};
    bool preorder(const IR::MethodCallStatement *mcs) override {
        std::cout << "MethodCallStatement *mcs = " << mcs << std::endl;
        std::cout << "MethodCallStatement *mcs->methodCall = " << mcs->methodCall << std::endl; return true;
    };
    bool preorder(const IR::IfStatement *ifs) override {std::cout << "IfStatement *if = " << ifs << std::endl; return true;};
    bool preorder(const IR::TypeNameExpression *t) override {std::cout << "TypeNameExpression *t = " << t << std::endl; return true;};
    bool preorder(const IR::ConstructorCallExpression *cce) override {std::cout << "ConstructorCallExpression *cce = " << cce << std::endl; return true;};
    bool preorder(const IR::NamedExpression *ne) override {std::cout << "NamedExpression *ne = " << ne << std::endl; return true;};
    bool preorder(const IR::DefaultExpression *dftexpr) override {std::cout << "DefaultExpression *dftexpr = " << dftexpr << std::endl; return true;};
    bool preorder(const IR::Declaration_Instance *di) override {std::cout << "Declaration_Instance *d = " << di << std::endl; return true;};
    
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
