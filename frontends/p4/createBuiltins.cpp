/*
Copyright 2013-present Barefoot Networks, Inc.

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

#include "createBuiltins.h"
#include "ir/ir.h"
#include "frontends/p4/coreLibrary.h"

namespace P4 {
void CreateBuiltins::postorder(IR::P4Parser* parser) {
    std::cout << "=====================Table Info========================" << std::endl;
    parser->states.push_back(new IR::ParserState(IR::ParserState::accept, nullptr));
    parser->states.push_back(new IR::ParserState(IR::ParserState::reject, nullptr));
}

void CreateBuiltins::postorder(IR::ActionListElement* element) {
    // convert path expressions to method calls
    // actions = { a; b; }
    // becomes
    // action = { a(); b(); }
    // std::cout << "CreateBuiltins::postorder(IR::ActionListElement* element = " << element << std::endl;
    if (element->expression->is<IR::PathExpression>())
        element->expression = new IR::MethodCallExpression(
            element->expression->srcInfo, element->expression,
            new IR::Vector<IR::Type>(), new IR::Vector<IR::Argument>());
}

void CreateBuiltins::postorder(IR::ExpressionValue* expression) {
    // std::cout << "CreateBuiltins::postorder(IR::ExpressionValue* expression = " << expression << std::endl;
    // convert a default_action = a; into
    // default_action = a();
    auto prop = findContext<IR::Property>();
    if (prop != nullptr &&
        prop->name == IR::TableProperties::defaultActionPropertyName &&
        expression->expression->is<IR::PathExpression>())
        expression->expression = new IR::MethodCallExpression(
            expression->expression->srcInfo, expression->expression,
            new IR::Vector<IR::Type>(), new IR::Vector<IR::Argument>());
}

void CreateBuiltins::postorder(IR::Entry* entry) {
  // std::cout << "CreateBuiltins::postorder(IR::Entry* entry = " << entry << std::endl;
  // convert a const table entry with action "a;" into "a();"
  if (entry->action->is<IR::PathExpression>())
    entry->action = new IR::MethodCallExpression(
      entry->action->srcInfo, entry->action,
      new IR::Vector<IR::Type>(), new IR::Vector<IR::Argument>());
}

void CreateBuiltins::postorder(IR::ParserState* state) {
    // std::cout << "CreateBuiltins::postorder(IR::ParserState* state = " << state << std::endl;
    if (state->selectExpression == nullptr) {
        warning(ErrorType::WARN_PARSER_TRANSITION, "%1%: implicit transition to `reject'", state);
        state->selectExpression = new IR::PathExpression(IR::ParserState::reject);
    }
}

void CreateBuiltins::postorder(IR::ActionList* actions) {
    // std::cout << "CreateBuiltins::postorder(IR::ActionList* actions = " << actions << std::endl;
    if (!addNoAction)
        return;
    auto decl = actions->getDeclaration(P4::P4CoreLibrary::instance.noAction.str());
    if (decl != nullptr)
        return;
    actions->push_back(
        new IR::ActionListElement(
            new IR::Annotations(
                {new IR::Annotation(IR::Annotation::defaultOnlyAnnotation, {}, false)}),
            new IR::MethodCallExpression(
                new IR::PathExpression(P4::P4CoreLibrary::instance.noAction.Id(actions->srcInfo)),
                new IR::Vector<IR::Type>(), new IR::Vector<IR::Argument>())));
}

bool CreateBuiltins::preorder(IR::P4Table* table) {
    std::cout << "table name is " << table->getName() << std::endl;
    if (table->getKey()->keyElements.size() != 0) {
        for (int i = 0; i < table->getKey()->keyElements.size(); i++) {
            std::cout << "no. " << (i + 1) << " key is " << table->getKey()->keyElements[i]->expression 
            << " with match type " << table->getKey()->keyElements[i]->matchType << std::endl;
        }
    } else 
        std::cout << "this table does not have match keys." << std::endl;
    if (table->getSizeProperty() != nullptr)
        std::cout << "table size is " << table->getSizeProperty() << std::endl;
    else 
        std::cout << "this table does not have size." << std::endl;
    if (table->getActionList()->size() != 0) 
        std::cout << "table action list is " << table->getActionList() << std::endl;
    else
        std::cout << "this table does not have actions." << std::endl;
    std::cout << std::endl;

    addNoAction = false;
    if (table->getDefaultAction() == nullptr)
        addNoAction = true;
    return true;
}

void CreateBuiltins::postorder(IR::TableProperties* properties) {
    // std::cout << "CreateBuiltins::postorder(IR::TableProperties* properties = " << properties << std::endl;
    if (!addNoAction)
        return;
    auto act = new IR::PathExpression(P4::P4CoreLibrary::instance.noAction.Id(properties->srcInfo));
    auto args = new IR::Vector<IR::Argument>();
    auto methodCall = new IR::MethodCallExpression(act, args);
    auto prop = new IR::Property(
        IR::ID(IR::TableProperties::defaultActionPropertyName),
        new IR::ExpressionValue(methodCall),
        /* isConstant = */ false);
    properties->properties.push_back(prop);
}

}  // namespace P4
