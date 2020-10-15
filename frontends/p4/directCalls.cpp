#include "directCalls.h"

namespace P4 {

const IR::Node* DoInstantiateCalls::preorder(IR::Type_Header* type_header) {
    std::cout << "++++++ Header name = " << type_header->getName() << std::endl;
    std::cout << "Header members:";
    for (int i = 0; i < type_header->fields.size(); i++) {
        std::cout << type_header->fields[i]->getName() << ";";
    }
    std::cout << std::endl;
    return type_header;
}

const IR::Node* DoInstantiateCalls::preorder(IR::Type_Struct* type_struct) {
    if (type_struct->getName() == cstring("standard_metadata_t")) {
        return type_struct;
    }
    std::cout << "++++++ Struct name = " << type_struct->getName() << std::endl;
    std::cout << "Struct members:";
    for (int i = 0; i < type_struct->fields.size(); i++) {
        std::cout << type_struct->fields[i]->getName() << ";";
    }
    std::cout << std::endl;
    return type_struct;
}


const IR::Node* DoInstantiateCalls::preorder(IR::P4Table* table) {
    // Add table match into the tableInfo_map
    std::cout << "+++++++++++++++Table name = " << table->getName() << std::endl;
    std::cout << "Match portion:";
    if (table->getKey()->keyElements.size() != 0) {
        for (int i = 0; i < table->getKey()->keyElements.size(); i++) {
            std::cout << table->getKey()->keyElements[i]->expression;
        }
    }
    std::cout << std::endl;
    std::cout << "Action portion:";
    if (table->getActionList()->size() != 0) {
        for (int i = 0; i < table->getActionList()->actionList.size(); i++) {
            if (table->getActionList()->actionList[i]->toString() != cstring("NoAction")) {
                std::cout << table->getActionList()->actionList[i]->toString() << ";";
            }
        }
    }
    std::cout << std::endl;

    return table;
}


const IR::Node* DoInstantiateCalls::preorder(IR::P4Action* action) {
    std::vector<cstring> para_vec;
    std::vector<cstring> body_vec;
    for (int i = 0; i < action->parameters->size(); i++) {
        std::cout << action->parameters[i].toString() << std::endl;
        para_vec.push_back(action->parameters[i].toString());
    }
    std::cout << "Action body = " << action->body << std::endl;
    for (int i = 0; i < action->body->components.size(); i++) {
         std::cout << "action->body->components[i]->getNode()->node_type_name()" << action->body->components[i]->getNode()->node_type_name() << std::endl;
         std::cout << "action->body->components[i]->getNode() = " << action->body->components[i]->getNode() << std::endl;
    }
    // TODO: add vars inside one action into vector
    return action;
}

// void DoInstantiateCalls::print_tableInfo_map() {
//     for(std::map<cstring, TableInfo>::iterator it = tableInfo_map.begin(); it != tableInfo_map.end(); it++) {
//         std::cout << "+++++++++++++++Table name = " << it->first << std::endl;
//         for (int i = 0; i < it->second.match_portion.size(); i++) {
//             std::cout << it->second.match_portion[i] << " ";
//         }
//         std::cout << std::endl;
//         for (int i = 0; i < it->second.action_portion.size(); i++) {
//             std::cout << it->second.action_portion[i] << " ";
//         }
//         std::cout << std::endl;
//     }
// }
// 
// void DoInstantiateCalls::print_headerInfo_map() {
// }
// 
// void DoInstantiateCalls::print_structInfo_map() {
// }
// 
// void DoInstantiateCalls::print_actionInfo_map() {
// }

const IR::Node* DoInstantiateCalls::postorder(IR::P4Parser* parser) {
    // std::cout << "DoInstantiateCalls::postorder(IR::P4Parser* parser = " << parser << std::endl;
    insert.append(parser->parserLocals);
    parser->parserLocals = insert;
    insert.clear();
    return parser;
}

const IR::Node* DoInstantiateCalls::postorder(IR::P4Control* control) {
    if (output_control == 0) {
        output_control = 1;
        std::cout << "=====================Control Block Info========================" << std::endl;
    }
    std::cout << "control block name is " << control->getName() << std::endl;
    std::cout << "control block body is " << control->body << std::endl;
    std::cout << "control->body->components.size() = " << control->body->components.size() << std::endl;
    for (int i = 0; i < control->body->components.size(); i++) {
        std::cout << "control->body->components[i] = " << control->body->components[i] << std::endl;
        std::cout << "control->body->components[i]->getNode()->node_type_name() = " << control->body->components[i]->getNode()->node_type_name() << std::endl;
        if (auto switch_ptr = control->body->components[i]->to<IR::SwitchStatement>()) {
           std::cout << "==================Output more about the block info==================" << std::endl;
           std::cout << "switch_ptr->expression->expression = " << switch_ptr->expression << std::endl;
           for (int j = 0; j < switch_ptr->cases.size(); j++) {
               std::cout << "switch_ptr->cases[j]->label = " << switch_ptr->cases[j]->label << std::endl;
               std::cout << "switch_ptr->cases[j]->statement = " << switch_ptr->cases[j]->statement << std::endl;
           }
        } else {
        }
    }
    std::cout << "\n";
    insert.append(control->controlLocals);
    control->controlLocals = insert;
    insert.clear();
    return control;
}

const IR::Node* DoInstantiateCalls::postorder(IR::MethodCallExpression* expression) {
    // std::cout << "DoInstantiateCalls::postorder(IR::MethodCallExpression* expression = " << expression << std::endl;
    // Identify type.apply(...) methods
    auto mem = expression->method->to<IR::Member>();
    if (mem == nullptr)
        return expression;
    auto tn = mem->expr->to<IR::TypeNameExpression>();
    if (tn == nullptr)
        return expression;

    auto ref = refMap->getDeclaration(tn->typeName->path, true);
    if (!ref->is<IR::P4Control>() && !ref->is<IR::P4Parser>()) {
        ::error("%1%: cannot invoke method of %2%", expression, ref);
        return expression;
    }

    auto name = refMap->newName(tn->typeName->path->name + "_inst");
    LOG3("Inserting instance " << name);
    auto annos = new IR::Annotations();
    annos->add(new IR::Annotation(
        IR::Annotation::nameAnnotation,
        { new IR::StringLiteral(tn->typeName->path->toString()) }, false));
    auto inst = new IR::Declaration_Instance(
        expression->srcInfo, IR::ID(name), annos,
        tn->typeName->clone(), new IR::Vector<IR::Argument>());
    insert.push_back(inst);

    auto path = new IR::PathExpression(expression->srcInfo,
                                       new IR::Path(IR::ID(expression->srcInfo, name)));
    expression->method = new IR::Member(path, mem->member);
    return expression;
}

}  // namespace P4
