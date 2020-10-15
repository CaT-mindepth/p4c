#include "directCalls.h"
#include <fstream>

namespace P4 {

class GetPktMember : public Transform {
    public:
        std::vector<cstring> pkt_vec;
        bool not_in_vec(cstring s) {
            for (int i = 0; i < pkt_vec.size(); i++) {
                if (pkt_vec[i] == s) {
                    return false;
                }
            }
            return true;
        }
        void print_vec() {
            std::ofstream file_to_print;
            file_to_print.open("/tmp/example.txt", std::ofstream::app);
            file_to_print << "fields modified within an Action:";
            for (int i = 0; i < pkt_vec.size(); i++) {
                file_to_print << pkt_vec[i] << ";";
            }
            file_to_print << "\n---------\n";
            file_to_print.close();
        }
        bool exist_dot(cstring s) {
            for (int i = 0; i < s.size(); i++) {
                if (s[i] == '.') {
                    return true;
                }
            }
            return false;
        }
        // We only record which pkt field is used in this particular action
        const IR::Node* preorder(IR::AssignmentStatement *as) override {if (exist_dot(as->left->toString()) and not_in_vec(as->left->toString())) { pkt_vec.push_back(as->left->toString());}
                                                                        if (exist_dot(as->right->toString()) and not_in_vec(as->right->toString())) { pkt_vec.push_back(as->right->toString());}
                                                                        return as;}
        const IR::Node* preorder(IR::Operation_Binary *expr) override {if (exist_dot(expr->left->toString()) and not_in_vec(expr->left->toString())) { pkt_vec.push_back(expr->left->toString());}
                                                                        if (exist_dot(expr->right->toString()) and not_in_vec(expr->right->toString())) { pkt_vec.push_back(expr->right->toString());}
                                                                       return expr;};
        const IR::Node* preorder(IR::Neg *expr) override {return expr;};
        const IR::Node* preorder(IR::Cmpl *expr) override {return expr;};
        const IR::Node* preorder(IR::LNot *expr) override {std::cout << "LNot *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Mul *expr) override {std::cout << "Mul *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Div *expr) override {std::cout << "Div *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Mod *expr) override {std::cout << "Mod *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Add *expr) override {std::cout << "Add expr->left = " << expr->left << std::endl; 
                                                          std::cout << "expr->right = " << expr->right << std::endl;
                                                          return expr;};
        const IR::Node* preorder(IR::AddSat *expr) override {std::cout << "AddSat *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Sub *expr) override {std::cout << "Sub *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::SubSat *expr) override {std::cout << "SubSat *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Shl *expr) override {std::cout << "Shl *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Shr *expr) override {std::cout << "Shr *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Equ *expr) override {if (exist_dot(expr->left->toString()) and not_in_vec(expr->left->toString())) { pkt_vec.push_back(expr->left->toString());}
                                                          if (exist_dot(expr->right->toString()) and not_in_vec(expr->right->toString())) { pkt_vec.push_back(expr->right->toString());}
                                                          return expr;};
        const IR::Node* preorder(IR::Neq *expr) override {std::cout << "Neq *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Lss *expr) override {std::cout << "Lss *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Leq *expr) override {std::cout << "Leq *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Grt *expr) override {std::cout << "Grt *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Geq *expr) override {std::cout << "Geq *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::BAnd *expr) override {std::cout << "BAnd *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::BOr *expr) override {std::cout << "BOr *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::BXor *expr) override {std::cout << "BXor *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::LAnd *expr) override {std::cout << "LAnd *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::LOr *expr) override {std::cout << "LOr *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Concat *expr) override {std::cout << "Concat *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Mask *expr) override {std::cout << "Mask *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Range *expr) override {std::cout << "Range *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::ArrayIndex *expr) override {std::cout << "ArrayIndex *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Slice *expr) override {std::cout << "Slice *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Mux *expr) override {std::cout << "Mux *expr = " << expr << std::endl; return expr;};
        const IR::Node* preorder(IR::Cast *expr) override {std::cout << "Cast *expr = " << expr << std::endl; return expr;};
};

const IR::Node* DoInstantiateCalls::preorder(IR::Type_Header* type_header) {
    std::ofstream file_to_print;
    if (!output_file) {
        output_file = 1;
        file_to_print.open("/tmp/example.txt");
    } else {
        file_to_print.open("/tmp/example.txt", std::ofstream::app);
    }
    file_to_print << "Header name = " << type_header->getName() << std::endl;
    file_to_print << "Header members:";
    for (int i = 0; i < type_header->fields.size(); i++) {
        file_to_print << type_header->fields[i]->getName() << ";";
    }
    file_to_print << "\n---------\n";
    file_to_print.close();
    return type_header;
}

const IR::Node* DoInstantiateCalls::preorder(IR::Type_Struct* type_struct) {
    if (type_struct->getName() == cstring("standard_metadata_t")) {
        return type_struct;
    }
    std::ofstream file_to_print;
    if (!output_file) {
        output_file = 1;
        file_to_print.open("/tmp/example.txt");
    } else {
        file_to_print.open("/tmp/example.txt", std::ofstream::app);
    }
    file_to_print << "Struct name = " << type_struct->getName() << std::endl;
    file_to_print << "Struct members:";
    for (int i = 0; i < type_struct->fields.size(); i++) {
        file_to_print << type_struct->fields[i]->getName() << ";";
    }
    file_to_print << "\n---------\n";
    file_to_print.close();
    return type_struct;
}


const IR::Node* DoInstantiateCalls::preorder(IR::P4Table* table) {
    // Add table match into the tableInfo_map
    std::ofstream file_to_print;
    if (!output_file) {
        file_to_print.open("/tmp/example.txt");
        output_file = 1;
    } else {
        file_to_print.open("/tmp/example.txt", std::ofstream::app);
    }
    file_to_print << "Table name = " << table->getName() << std::endl;
    file_to_print << "Match portion:";
    if (table->getKey()->keyElements.size() != 0) {
        for (int i = 0; i < table->getKey()->keyElements.size(); i++) {
            file_to_print << table->getKey()->keyElements[i]->expression;
        }
    }
    file_to_print << std::endl;
    file_to_print << "Action portion:";
    if (table->getActionList()->size() != 0) {
        for (int i = 0; i < table->getActionList()->actionList.size(); i++) {
            if (table->getActionList()->actionList[i]->toString() != cstring("NoAction")) {
                file_to_print << table->getActionList()->actionList[i]->toString() << ";";
            }
        }
    }
    file_to_print << "\n---------" << std::endl;
    file_to_print.close();
    return table;
}


const IR::Node* DoInstantiateCalls::preorder(IR::P4Action* action) {
   if (action->getName() == "NoAction") {
       return action;
   }
   std::ofstream file_to_print;
   file_to_print.open("/tmp/example.txt", std::ofstream::app);
   file_to_print << "Action name = " << action->getName() << std::endl;
   GetPktMember gpm;
   for (int i = 0; i < action->body->components.size(); i++) {
       IR::Node *copy_node = action->body->components[i]->getNode()->clone();
       auto fin_node = copy_node->apply(gpm);
   }
   gpm.print_vec();
   return action;
}

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
