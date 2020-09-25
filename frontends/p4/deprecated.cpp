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

class FinalCodeFormat : public Transform {
    public:
        const IR::Node* preorder(IR::MethodCallStatement *mcs) override {return nullptr;};
};

class CheckGetMember : public Transform {
    const ReferenceMap* refMap;
    std::map<cstring, cstring> rename_map;
public:
    explicit CheckGetMember(const ReferenceMap* refMap): refMap(refMap)
    { CHECK_NULL(refMap); setName("CheckGetMember"); }
    std::string output_str = "";

//    void warnIfGetMember(const IR::IAnnotated* declaration, const IR::Node* errorNode) {};

    // Transform
    //const IR::Node*  preorder(IR::Constant *c) override { return c;};
        // bool preorder(const IR::PathExpression* path) override {std::cout << "PathExpression* path->path->name = " << path->path->name << std::endl; return true;};
    // const IR::Node* preorder(IR::Type_Name* name) override {std::cout << "Type_Name* name = " << name << std::endl; return name; };
    // const IR::Node* preorder(IR::P4Action* action) override {std::cout << "P4Action action = " << action << std::endl; return action;};
    const IR::Node* preorder(IR::Expression* expression) override {
        std::map<cstring, cstring>::iterator it = rename_map.find(expression->toString());
        // std::cout << "(it != rename_map.end()) = " << (it != rename_map.end()) << std::endl;
        if (it != rename_map.end()) {
            expression = new IR::PathExpression(cstring(it->second));
        }
        return expression;
    };
    // const IR::Node* preorder(IR::P4Parser *p) override {std::cout << "P4Parser *p4parser = " << p << std::endl; return p;};
    // const IR::Node* preorder(IR::ParserState *ps) override {std::cout << "ParserState *ps = " << ps << std::endl; return ps;};
    // const IR::Node* preorder(IR::P4ValueSet *pvs) override {std::cout << "P4ValueSet *pvs = " << pvs << std::endl; return pvs;};
    // const IR::Node* preorder(IR::SelectExpression *se) override {std::cout << "SelectExpression *se = " << se << std::endl; return se;};
    // const IR::Node* preorder(IR::SelectCase *sc) override {std::cout << "SelectCase *sc = " << sc << std::endl; return sc;};
    // const IR::Node* preorder(IR::P4Control *c) override {std::cout << "P4Control *c = " << c << std::endl; return c;};
    // const IR::Node* preorder(IR::Type_Extern *t) override {std::cout << "Type_Extern *t = " << t << std::endl; return t;};
    // const IR::Node* preorder(IR::Type_Method *t) override {std::cout << "Type_Method *t = " << t << std::endl; return t;};
    // const IR::Node* preorder(IR::Method *method) override {std::cout << "Method *method = " << method << std::endl; return method;};
    // const IR::Node* preorder(IR::Function *function) override {std::cout << "Function *function = " << function << std::endl; return function;};
    // const IR::Node* preorder(IR::P4Table *p4table) override {std::cout << "P4Table *p4table = " << p4table << std::endl; return p4table;};
    // const IR::Node* preorder(IR::Property *p) override {std::cout << "Property *p = " << p << std::endl; return p;};
    // const IR::Node* preorder(IR::ActionList *acl) override {std::cout << "ActionList *acl = " << acl << std::endl; return acl;};
    // const IR::Node* preorder(IR::Entry *e) override {std::cout << "Entry *e = " << e << std::endl; return e;};
    // const IR::Node* preorder(IR::EntriesList *el) override {std::cout << "EntriesList *el = " << el << std::endl; return el;};
    // const IR::Node* preorder(IR::Key *key) override {std::cout << "Key *key = " << key << std::endl; return key;};
    // const IR::Node* preorder(IR::KeyElement *ke) override {std::cout << "KeyElement *ke = " << ke << std::endl; return ke;};
    // const IR::Node* preorder(IR::ExpressionValue *ev) override {std::cout << "ExpressionValue *ev = " << ev << std::endl; return ev;};
    const IR::Node* preorder(IR::MethodCallExpression *mce) override {
        // std::cout << "MethodCallExpression *mce = " << mce << std::endl;
        // std::cout << "MethodCallExpression *mce->method = " << mce->method << std::endl;
        // std::cout << "mce->arguments->size() = " << mce->arguments->size() << std::endl;
        // std::cout << "mce->argumentsi[0].size() = " << mce->arguments[0].size() << std::endl;
        // for (int i = 0; i < mce->arguments->size(); i++) {
        //     std::cout << "mce->arguments[0][i] = " << mce->arguments[0][i]->toString() << std::endl;
        // }
        cstring value_str = mce->method->toString();
        cstring key_str;
        if (value_str.find("read") != nullptr) {
           key_str = mce->arguments[0][0]->toString();
        } else {
           assert(value_str.find("write") != nullptr);
           key_str = mce->arguments[0][1]->toString();
        }
        value_str = value_str.substr(0, value_str.find('.') - value_str.begin());
        std::map<cstring, cstring>::iterator it = rename_map.find(key_str);
        if (it == rename_map.end()) {
            rename_map[key_str] = value_str;
        }
        // mce = nullptr;
        return mce;
    };
    // const IR::Node* preorder(IR::ListExpression *le) override {std::cout << "ListExpression *le = " << le << std::endl; return le;};
    // const IR::Node* preorder(IR::BlockStatement *b) override {std::cout << "BlockStatement *b = " << b << std::endl; return b;};
    // const IR::Node* preorder(IR::EmptyStatement *emptystmt) override {std::cout << "EmptyStatement *emptystmt = " << emptystmt << std::endl; return emptystmt;};
    // const IR::Node* preorder(IR::ExitStatement *exitstmt) override {std::cout << "ExitStatement *exitstmt = " << exitstmt << std::endl; return exitstmt;};
    // const IR::Node* preorder(IR::ReturnStatement *r) override {std::cout << "ReturnStatement * = " << r << std::endl; return r;};
    const IR::Node* preorder(IR::AssignmentStatement *as) override {std::cout << "AssignmentStatement *as = " << as << std::endl; return as;};
    // const IR::Node* preorder(IR::MethodCallStatement *mcs) override {
    //     std::cout << "MethodCallStatement *mcs = " << mcs << std::endl;
    //     std::cout << "MethodCallStatement *mcs->methodCall = " << mcs->methodCall << std::endl;
    //     return mcs;
    // };
    // const IR::Node* preorder(IR::IfStatement *ifs) override {std::cout << "IfStatement *if = " << ifs << std::endl; return ifs;};
    // const IR::Node* preorder(IR::Operation_Binary *expr) override {std::cout << "Operation_Binary *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Operation_Ternary *expr) override {std::cout << "Operation_Ternary *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Neg *expr) override {std::cout << "Neg *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Cmpl *expr) override {std::cout << "Cmpl *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::LNot *expr) override {std::cout << "LNot *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Mul *expr) override {std::cout << "Mul *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Div *expr) override {std::cout << "Div *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Mod *expr) override {std::cout << "Mod *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Add *expr) override {std::cout << "Add *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::AddSat *expr) override {std::cout << "AddSat *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Sub *expr) override {std::cout << "Sub *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::SubSat *expr) override {std::cout << "SubSat *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Shl *expr) override {std::cout << "Shl *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Shr *expr) override {std::cout << "Shr *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Equ *expr) override {std::cout << "Equ *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Neq *expr) override {std::cout << "Neq *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Lss *expr) override {std::cout << "Lss *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Leq *expr) override {std::cout << "Leq *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Grt *expr) override {std::cout << "Grt *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Geq *expr) override {std::cout << "Geq *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::BAnd *expr) override {std::cout << "BAnd *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::BOr *expr) override {std::cout << "BOr *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::BXor *expr) override {std::cout << "BXor *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::LAnd *expr) override {std::cout << "LAnd *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::LOr *expr) override {std::cout << "LOr *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Concat *expr) override {std::cout << "Concat *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Mask *expr) override {std::cout << "Mask *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Range *expr) override {std::cout << "Range *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::ArrayIndex *expr) override {std::cout << "ArrayIndex *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Slice *expr) override {std::cout << "Slice *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Mux *expr) override {std::cout << "Mux *expr = " << expr << std::endl; return expr;};
    // const IR::Node* preorder(IR::Cast *expr) override {std::cout << "Cast *expr = " << expr << std::endl; return expr;};
    const IR::Node* preorder(IR::Member *m) override {
        // std::cout << "Member *m = " << m << std::endl;
        // std::cout << "m->member = " << m->member << std::endl;
        if (m->member.toString() != cstring("read") and m->member.toString() != cstring("write")) {
            m->expr = new IR::PathExpression(cstring("pkt"));
        }
        return m;
    };

    // const IR::Node* preorder(IR::TypeNameExpression *t) override {std::cout << "TypeNameExpression *t = " << t << std::endl; return t;};
    // const IR::Node* preorder(IR::ConstructorCallExpression *cce) override {std::cout << "ConstructorCallExpression *cce = " << cce << std::endl; return cce;};
    // const IR::Node* preorder(IR::NamedExpression *ne) override {std::cout << "NamedExpression *ne = " << ne << std::endl; return ne;};
    // const IR::Node* preorder(IR::DefaultExpression *dftexpr) override {std::cout << "DefaultExpression *dftexpr = " << dftexpr << std::endl; return dftexpr;};
    // const IR::Node* preorder(IR::BoolLiteral *bl) override {std::cout << "BoolLiteral *bl = " << bl << std::endl; return bl;};
    // const IR::Node* preorder(IR::StringLiteral *str) override {std::cout << "StringLiteral *str = " << str << std::endl; return str;};
    // const IR::Node* preorder(IR::Parameter *p) override {std::cout << "Parameter *p = " << p << std::endl; return p;};
    // const IR::Node* preorder(IR::ParameterList *p) override {std::cout << "ParameterList *p = " << p << std::endl; return p;};
    // const IR::Node* preorder(IR::TypeParameters *tp) override {std::cout << "TypeParameters *tp = " << tp << std::endl; return tp;};
    // const IR::Node* preorder(IR::Argument *arg) override {std::cout << "Argument *arg = " << arg << std::endl; return arg;};
    // const IR::Node* preorder(IR::Declaration_Instance *di) override {std::cout << "Declaration_Instance *d = " << di << std::endl; return di;};
    const IR::Node* preorder(IR::Declaration_Variable *declaration_var) override {
        return nullptr;
    }
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
    if (output_action == 0) {
        output_action = 1;
        std::cout << "=====================Action Info========================" << std::endl;
    }
    std::cout << "Action name = " << action->getName() << std::endl;
    std::cout << "Action body = " << action->body << std::endl;
    for (int i = 0; i < action->body->components.size(); i++) { 
        if (action->body->components[i]->getNode()->node_type_name() == "BlockStatement") {
            CheckGetMember chgm(this->refMap); 
            IR::Node *copy_node = action->body->components[i]->getNode()->clone();
            auto mid_node = copy_node->apply(chgm);
            FinalCodeFormat fcf;
            auto fin_node = mid_node->apply(fcf);
            // std::cout << "=========================" << std::endl;
            // std::cout << "mid_node = " << mid_node << std::endl;
            std::cout << "Parsed action body = " << fin_node << std::endl;
            // std::cout << "action->body->components[i]->getNode() = " << action->body->components[i]->getNode() << std::endl;
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
